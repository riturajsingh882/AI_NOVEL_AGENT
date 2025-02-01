import os
import yaml
import json
from openai import OpenAI
from datetime import datetime
import logging
from pathlib import Path

class NovelGenerator:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.base_dir / 'writer.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Novel Generator")
        
        self.load_config()
        self.load_progress()
        self.initialize_client()
        self.verify_chapter_file()

    def initialize_client(self):
        """Initialize OpenAI client with config validation"""
        try:
            self.client = OpenAI(
                base_url=self.api_config['base_url'],
                api_key=self.api_config['api_key']
            )
            # Test API connectivity
            self.client.models.list()
        except KeyError as e:
            self.logger.error(f"Missing config key: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"API connection failed: {str(e)}")
            raise

    def load_config(self):
        """Load configuration with validation"""
        config_path = self.base_dir / 'config' / 'api_config.yaml'
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
                self.api_config = config['KLUSTER_API']
                # Validate required parameters
                if not all(k in self.api_config for k in ['base_url', 'api_key', 'model', 'parameters']):
                    raise ValueError("Invalid API config structure")
        except Exception as e:
            self.logger.error(f"Config load failed: {str(e)}")
            raise

    def load_progress(self):
        """Load progress with validation and automatic repair"""
        self.progress_path = self.base_dir / 'book_progress.json'
        default_progress = {
            "current_chapter": 1,
            "current_page": 1,
            "total_pages": 200,
            "last_commit": None,
            "chapter_titles": {}
        }
        
        try:
            if self.progress_path.exists():
                with open(self.progress_path, 'r') as f:
                    self.progress = json.load(f)
                
                # Validate structure
                required_keys = ['current_chapter', 'current_page', 'total_pages', 'last_commit']
                if not all(k in self.progress for k in required_keys):
                    raise ValueError("Invalid progress structure")
                
                # Repair missing chapter titles
                if 'chapter_titles' not in self.progress:
                    self.progress['chapter_titles'] = {}
                
                # Validate dates
                if self.progress['last_commit']:
                    last_date = datetime.fromisoformat(self.progress['last_commit'])
                    if last_date > datetime.now():
                        self.logger.warning("Future timestamp detected! Resetting progress.")
                        raise ValueError("Invalid future timestamp")
            else:
                raise FileNotFoundError

        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"Progress error: {str(e)} - Initializing defaults")
            self.progress = default_progress
            self.save_progress()

    def get_chapter_title(self, chapter_num):
        """Get title from cache or file with validation"""
        # Check cached titles first
        if str(chapter_num) in self.progress['chapter_titles']:
            return self.progress['chapter_titles'][str(chapter_num)]
        
        # Fallback to file extraction
        chap_file = self.base_dir / 'chapters' / f"chapter_{chapter_num:02d}.md"
        try:
            with open(chap_file, 'r') as f:
                first_line = f.readline().strip()
                if first_line.startswith('# Chapter'):
                    title = first_line.split(':', 1)[1].strip()
                    # Cache the title
                    self.progress['chapter_titles'][str(chapter_num)] = title
                    self.save_progress()
                    return title
        except FileNotFoundError:
            pass
        
        # Final fallback
        return f"Chapter {chapter_num}"

    def verify_chapter_file(self):
        """Create new chapter file with validated title"""
        chap_num = self.progress['current_chapter']
        chap_file = self.base_dir / 'chapters' / f"chapter_{chap_num:02d}.md"
        
        if not chap_file.exists():
            self.logger.info(f"Creating new chapter file: {chap_file}")
            title = self.generate_chapter_title()
            
            # Store title in progress
            self.progress['chapter_titles'][str(chap_num)] = title
            self.save_progress()
            
            with open(chap_file, 'w') as f:
                f.write(f"# Chapter {chap_num}: {title}\n\n")

    def generate_chapter_title(self):
        """Generate AI-powered chapter title with validation"""
        try:
            # Get context from previous chapter
            context = ""
            if self.progress['current_chapter'] > 1:
                prev_chapter = self.progress['current_chapter'] - 1
                context = self.get_previous_chapter_context(prev_chapter)
            
            prompt = f"""Generate a compelling chapter title based on this context:
            {context}
            
            Requirements:
            - 2-5 words
            - Mysterious tone
            - No numbers or special characters
            - Example format: 'The Whispering Woods'
            - Return ONLY the title, no quotes"""
            
            response = self.client.chat.completions.create(
                model=self.api_config['model'],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=25,
                temperature=0.7
            )
            
            raw_title = response.choices[0].message.content.strip()
            # Clean title
            clean_title = raw_title.split('\n')[0].strip('"').strip("'")
            # Remove chapter numbers
            clean_title = ''.join([c for c in clean_title if not c.isdigit()]).strip()
            
            if not clean_title:
                raise ValueError("Empty title generated")
                
            return clean_title
            
        except Exception as e:
            self.logger.error(f"Title generation failed: {str(e)}")
            return f"Chapter {self.progress['current_chapter']}"

    def get_previous_chapter_context(self, chapter_num):
        """Get context from previous chapter with validation"""
        chap_file = self.base_dir / 'chapters' / f"chapter_{chapter_num:02d}.md"
        try:
            if chap_file.exists() and chap_file.stat().st_size > 0:
                with open(chap_file, 'r') as f:
                    content = f.read()
                    return content[-1000:] if len(content) > 1000 else content
            return ""
        except Exception as e:
            self.logger.error(f"Context retrieval failed: {str(e)}")
            return ""

    def save_progress(self):
        """Save progress with atomic write"""
        try:
            temp_path = self.progress_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(self.progress, f, indent=2)
            temp_path.replace(self.progress_path)
        except Exception as e:
            self.logger.error(f"Progress save failed: {str(e)}")
            raise

    def get_previous_context(self):
        """Get context for continuation with validation"""
        try:
            chap_file = self.base_dir / 'chapters' / f"chapter_{self.progress['current_chapter']:02d}.md"
            if chap_file.exists() and chap_file.stat().st_size > 0:
                with open(chap_file, 'r') as f:
                    content = f.read()
                    return content[-2000:] if len(content) > 2000 else content
            return ""
        except Exception as e:
            self.logger.error(f"Context retrieval failed: {str(e)}")
            return ""

    def generate_text(self, prompt):
        """Generate text with enhanced error handling"""
        try:
            response = self.client.chat.completions.create(
                model=self.api_config['model'],
                messages=[
                    {"role": "system", "content": "You are a professional novelist."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.api_config['parameters']['max_tokens'],
                temperature=self.api_config['parameters']['temperature']
            )
            
            if not response.choices:
                raise ValueError("Empty API response")
                
            content = response.choices[0].message.content
            if not content.strip():
                raise ValueError("Empty content generated")
                
            return content
            
        except Exception as e:
            self.logger.error(f"Generation failed: {str(e)}")
            return None

    def remove_internal_page_numbers(self, content):
        """Clean content from unwanted numbering"""
        lines = []
        for line in content.split('\n'):
            clean_line = line.strip().lower()
            if clean_line.startswith('page ') or clean_line.startswith('chapter '):
                continue
            lines.append(line)
        return '\n'.join(lines)

    def create_daily_content(self):
        """Main content generation workflow"""
        try:
            context = self.get_previous_context()
            chapter_num = self.progress['current_chapter']
            chapter_title = self.get_chapter_title(chapter_num)
            
            prompt = f"""Continue the novel from exactly where it left off.
            Current Chapter: {chapter_num} ("{chapter_title}")
            Current Page: {self.progress['current_page']}
            
            Previous Context:
            {context}
            
            Write the next section (600-800 words). Requirements:
            - Keep existing chapter title: "{chapter_title}"
            - Maintain plot continuity
            - Preserve character voices
            - Include environmental details
            - NO page/chapter numbers in text
            - Markdown formatting for paragraphs only"""
            
            new_content = self.generate_text(prompt)
            if not new_content:
                raise ValueError("Content generation failed")
                
            cleaned_content = self.remove_internal_page_numbers(new_content)
            self.save_content(cleaned_content)
            self.update_progress()
            return True
            
        except Exception as e:
            self.logger.error(f"Daily content failed: {str(e)}", exc_info=True)
            return False

    def save_content(self, content):
        """Save content with validation"""
        if not content.strip():
            raise ValueError("Attempted to save empty content")
            
        current_page = self.progress['current_page']
        chapter_num = self.progress['current_chapter']
        chap_file = self.base_dir / 'chapters' / f"chapter_{chapter_num:02d}.md"
        
        try:
            with open(chap_file, 'a', encoding='utf-8') as f:
                f.write(f"\n## Page {current_page}\n")
                f.write(content.strip() + '\n')
        except Exception as e:
            self.logger.error(f"Content save failed: {str(e)}")
            raise

    def update_progress(self):
        """Update progress with chapter transition logic"""
        previous_page = self.progress['current_page']
        self.progress['current_page'] += 1
        
        # Configurable pages per chapter (default 10)
        pages_per_chapter = self.api_config.get('pages_per_chapter', 10)
        if previous_page % pages_per_chapter == 0:
            self.progress['current_chapter'] += 1
            self.verify_chapter_file()
            self.logger.info(f"Transitioned to Chapter {self.progress['current_chapter']}")
            
        self.progress['last_commit'] = datetime.now().isoformat()
        self.save_progress()