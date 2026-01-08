"""
WhatsApp Appeal Bot - Part 1: Configuration and Classes
Created: 2026-01-08 16:40:04 UTC
Author: xdexzzzkaryawan
Description: Core configuration, data models, and utility classes for WhatsApp Appeal Bot
"""

import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

class LogConfig:
    """Centralized logging configuration for the bot"""
    
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    LOG_LEVEL = logging.INFO
    
    @staticmethod
    def setup_logging(log_file: str = 'whatsapp_bot.log') -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('WhatsAppBot')
        logger.setLevel(LogConfig.LOG_LEVEL)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(LogConfig.LOG_LEVEL)
        file_formatter = logging.Formatter(LogConfig.LOG_FORMAT, LogConfig.DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(LogConfig.LOG_LEVEL)
        console_formatter = logging.Formatter(LogConfig.LOG_FORMAT, LogConfig.DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger


# ============================================================================
# ENUMERATIONS
# ============================================================================

class AppealStatus(Enum):
    """Enumeration for appeal status states"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class UserRole(Enum):
    """Enumeration for user roles in the system"""
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"


class MessageType(Enum):
    """Enumeration for different message types"""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    LOCATION = "location"
    CONTACT = "contact"


class BotCommand(Enum):
    """Enumeration for bot commands"""
    START = "/start"
    HELP = "/help"
    SUBMIT_APPEAL = "/appeal"
    CHECK_STATUS = "/status"
    CANCEL = "/cancel"
    MENU = "/menu"
    SETTINGS = "/settings"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class AppealDetails:
    """Data model for appeal details"""
    appeal_id: str
    user_id: str
    phone_number: str
    appeal_title: str
    appeal_description: str
    appeal_category: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: AppealStatus = AppealStatus.PENDING
    priority: str = "normal"
    attachments: List[str] = field(default_factory=list)
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert appeal details to dictionary"""
        return {
            'appeal_id': self.appeal_id,
            'user_id': self.user_id,
            'phone_number': self.phone_number,
            'appeal_title': self.appeal_title,
            'appeal_description': self.appeal_description,
            'appeal_category': self.appeal_category,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'status': self.status.value,
            'priority': self.priority,
            'attachments': self.attachments,
            'notes': self.notes
        }
    
    def to_json(self) -> str:
        """Convert appeal details to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class UserProfile:
    """Data model for user profile"""
    user_id: str
    phone_number: str
    name: str
    email: Optional[str] = None
    role: UserRole = UserRole.USER
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    preferences: Dict[str, Any] = field(default_factory=dict)
    appeals_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user profile to dictionary"""
        return {
            'user_id': self.user_id,
            'phone_number': self.phone_number,
            'name': self.name,
            'email': self.email,
            'role': self.role.value,
            'created_at': self.created_at.isoformat(),
            'last_active': self.last_active.isoformat(),
            'is_active': self.is_active,
            'preferences': self.preferences,
            'appeals_count': self.appeals_count
        }


@dataclass
class BotMessage:
    """Data model for bot messages"""
    message_id: str
    sender_id: str
    recipient_id: str
    message_text: str
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime = field(default_factory=datetime.utcnow)
    is_read: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def mark_as_read(self) -> None:
        """Mark message as read"""
        self.is_read = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'message_id': self.message_id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'message_text': self.message_text,
            'message_type': self.message_type.value,
            'timestamp': self.timestamp.isoformat(),
            'is_read': self.is_read,
            'metadata': self.metadata
        }


# ============================================================================
# BOT CONFIGURATION
# ============================================================================

class BotConfig:
    """Main bot configuration class"""
    
    # Bot Basic Settings
    BOT_NAME = "WhatsApp Appeal Bot"
    BOT_VERSION = "1.0.0"
    BOT_DESCRIPTION = "WhatsApp bot for handling user appeals and requests"
    BOT_AUTHOR = "xdexzzzkaryawan"
    
    # API Configuration
    API_BASE_URL = "https://api.whatsapp.com"
    API_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    
    # WhatsApp Configuration
    WHATSAPP_PHONE_NUMBER = None  # To be set from environment
    WHATSAPP_BUSINESS_ACCOUNT_ID = None  # To be set from environment
    WHATSAPP_ACCESS_TOKEN = None  # To be set from environment
    
    # Database Configuration
    DATABASE_TYPE = "sqlite"  # sqlite, mysql, postgresql
    DATABASE_HOST = "localhost"
    DATABASE_PORT = 3306
    DATABASE_NAME = "whatsapp_bot.db"
    DATABASE_USER = None
    DATABASE_PASSWORD = None
    
    # Message Configuration
    MESSAGE_QUEUE_SIZE = 1000
    MESSAGE_TIMEOUT = 300  # seconds
    MAX_MESSAGE_LENGTH = 4096
    
    # Appeal Configuration
    APPEAL_CATEGORIES = [
        "Technical Issue",
        "Account Problem",
        "Payment Issue",
        "General Inquiry",
        "Complaint",
        "Suggestion",
        "Other"
    ]
    
    APPEAL_PRIORITIES = ["low", "normal", "high", "urgent"]
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_PER_USER = 10  # messages per minute
    RATE_LIMIT_PER_HOUR = 100  # messages per hour
    
    # Response Templates
    RESPONSE_TEMPLATES = {
        'greeting': "Hello {name}! Welcome to {bot_name}. How can I help you today?",
        'help': "Here are the available commands:\n{commands}",
        'appeal_submitted': "Thank you! Your appeal #{appeal_id} has been submitted successfully.",
        'invalid_command': "Sorry, I didn't understand that. Type /help for available commands.",
        'error': "An error occurred. Please try again later.",
    }
    
    # Timezone
    TIMEZONE = "UTC"
    
    # Debug Mode
    DEBUG_MODE = False
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            'bot_name': cls.BOT_NAME,
            'bot_version': cls.BOT_VERSION,
            'bot_description': cls.BOT_DESCRIPTION,
            'api_timeout': cls.API_TIMEOUT,
            'max_retries': cls.MAX_RETRIES,
            'database_type': cls.DATABASE_TYPE,
            'message_queue_size': cls.MESSAGE_QUEUE_SIZE,
            'rate_limit_enabled': cls.RATE_LIMIT_ENABLED,
            'debug_mode': cls.DEBUG_MODE,
        }


# ============================================================================
# UTILITY CLASSES
# ============================================================================

class MessageBuilder:
    """Utility class for building formatted messages"""
    
    @staticmethod
    def build_menu_message() -> str:
        """Build main menu message"""
        menu = """
📋 *Main Menu*

1️⃣ Submit Appeal - /appeal
2️⃣ Check Status - /status
3️⃣ Get Help - /help
4️⃣ Settings - /settings

Type the command or number to proceed.
        """
        return menu.strip()
    
    @staticmethod
    def build_help_message() -> str:
        """Build help message"""
        help_text = """
🆘 *Available Commands*

/start - Start the bot
/appeal - Submit a new appeal
/status - Check your appeal status
/menu - Show main menu
/settings - Change preferences
/help - Show this help message
/cancel - Cancel current operation

For more information, type /menu
        """
        return help_text.strip()
    
    @staticmethod
    def build_appeal_form() -> str:
        """Build appeal submission form"""
        form = """
📝 *Submit Your Appeal*

Please provide the following information:

1. *Title* - Brief summary of your issue
2. *Category* - Select from the list
3. *Description* - Detailed explanation
4. *Attachments* (Optional) - Upload documents/images

What would you like to report?
        """
        return form.strip()
    
    @staticmethod
    def format_appeal_summary(appeal: AppealDetails) -> str:
        """Format appeal summary"""
        summary = f"""
📋 *Appeal Summary*

ID: {appeal.appeal_id}
Title: {appeal.appeal_title}
Category: {appeal.appeal_category}
Status: {appeal.status.value.upper()}
Priority: {appeal.priority.upper()}
Created: {appeal.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Description:
{appeal.appeal_description}
        """
        return summary.strip()


class ValidationHelper:
    """Utility class for data validation"""
    
    @staticmethod
    def is_valid_phone_number(phone: str) -> bool:
        """Validate phone number format"""
        # Remove common formatting characters
        cleaned = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        # Check if it's numeric and reasonable length
        return cleaned.isdigit() and 10 <= len(cleaned) <= 15
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_valid_appeal_title(title: str) -> bool:
        """Validate appeal title"""
        return 5 <= len(title) <= 200
    
    @staticmethod
    def is_valid_appeal_description(description: str) -> bool:
        """Validate appeal description"""
        return 10 <= len(description) <= 2000


class IDGenerator:
    """Utility class for generating unique IDs"""
    
    import uuid
    
    @staticmethod
    def generate_appeal_id() -> str:
        """Generate unique appeal ID"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        random_suffix = str(IDGenerator.uuid.uuid4())[:8].upper()
        return f"APPEAL-{timestamp}-{random_suffix}"
    
    @staticmethod
    def generate_user_id() -> str:
        """Generate unique user ID"""
        return f"USER-{IDGenerator.uuid.uuid4()}"
    
    @staticmethod
    def generate_message_id() -> str:
        """Generate unique message ID"""
        return f"MSG-{IDGenerator.uuid.uuid4()}"


class ErrorHandler:
    """Utility class for error handling"""
    
    class BotException(Exception):
        """Base exception for bot errors"""
        pass
    
    class ValidationError(BotException):
        """Raised when validation fails"""
        pass
    
    class APIError(BotException):
        """Raised when API call fails"""
        pass
    
    class DatabaseError(BotException):
        """Raised when database operation fails"""
        pass
    
    @staticmethod
    def handle_error(error: Exception, logger: logging.Logger) -> str:
        """Handle errors and return user-friendly message"""
        logger.error(f"Error occurred: {str(error)}", exc_info=True)
        
        if isinstance(error, ErrorHandler.ValidationError):
            return "Invalid input. Please check your data and try again."
        elif isinstance(error, ErrorHandler.APIError):
            return "Service temporarily unavailable. Please try again later."
        elif isinstance(error, ErrorHandler.DatabaseError):
            return "Database error. Please try again later."
        else:
            return "An unexpected error occurred. Please try again later."


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_bot() -> logging.Logger:
    """Initialize bot with logging and configuration"""
    logger = LogConfig.setup_logging()
    logger.info(f"Initializing {BotConfig.BOT_NAME} v{BotConfig.BOT_VERSION}")
    logger.info(f"Configuration: {json.dumps(BotConfig.to_dict(), indent=2)}")
    return logger


if __name__ == "__main__":
    # Test initialization
    logger = initialize_bot()
    logger.info("Bot Part 1 - Configuration and Classes loaded successfully")
    
    # Display configuration
    print("\n" + "="*60)
    print(f"{BotConfig.BOT_NAME} - Configuration Summary")
    print("="*60)
    print(f"Version: {BotConfig.BOT_VERSION}")
    print(f"Description: {BotConfig.BOT_DESCRIPTION}")
    print(f"Debug Mode: {BotConfig.DEBUG_MODE}")
    print(f"Database: {BotConfig.DATABASE_TYPE}")
    print("="*60 + "\n")
