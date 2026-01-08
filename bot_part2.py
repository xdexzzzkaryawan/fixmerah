"""
WhatsApp Appeal Bot Part 2 - Handlers and Logic
Handles advanced message processing, appeal management, and user interactions
Created: 2026-01-08 16:40:27 UTC
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AppealStatus(Enum):
    """Appeal status enumeration"""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    CLOSED = "closed"


class MessageType(Enum):
    """Message type enumeration"""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    LOCATION = "location"
    CONTACT = "contact"


@dataclass
class UserProfile:
    """User profile data structure"""
    user_id: str
    phone_number: str
    name: str
    email: Optional[str] = None
    created_at: str = None
    last_interaction: str = None
    total_appeals: int = 0
    verification_status: bool = False

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.last_interaction is None:
            self.last_interaction = datetime.utcnow().isoformat()


@dataclass
class Appeal:
    """Appeal data structure"""
    appeal_id: str
    user_id: str
    category: str
    subject: str
    description: str
    status: AppealStatus = AppealStatus.PENDING
    priority: str = "normal"
    attachments: List[str] = None
    created_at: str = None
    updated_at: str = None
    assigned_to: Optional[str] = None
    notes: List[str] = None
    resolution: Optional[str] = None

    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow().isoformat()
        if self.notes is None:
            self.notes = []


class MessageHandler:
    """Handles incoming and outgoing messages"""

    def __init__(self):
        self.message_queue: List[Dict] = []
        self.processed_messages: List[Dict] = []

    def parse_message(self, raw_message: Dict) -> Dict:
        """
        Parse raw WhatsApp message into structured format
        
        Args:
            raw_message: Raw message dictionary from WhatsApp
            
        Returns:
            Parsed message dictionary
        """
        try:
            parsed = {
                'message_id': raw_message.get('id'),
                'from_number': raw_message.get('from'),
                'timestamp': raw_message.get('timestamp', datetime.utcnow().isoformat()),
                'type': MessageType.TEXT.value,
                'content': raw_message.get('body', ''),
                'media': None,
                'processed': False
            }

            # Handle different message types
            if 'media' in raw_message:
                parsed['type'] = raw_message['media'].get('type', MessageType.IMAGE.value)
                parsed['media'] = raw_message['media']

            logger.info(f"Message parsed: {parsed['message_id']}")
            return parsed

        except Exception as e:
            logger.error(f"Error parsing message: {str(e)}")
            return None

    def extract_intent(self, message_content: str) -> Tuple[str, Dict]:
        """
        Extract user intent and parameters from message
        
        Args:
            message_content: Message text content
            
        Returns:
            Tuple of (intent, parameters)
        """
        content_lower = message_content.lower().strip()

        # Define intent patterns
        intent_patterns = {
            'create_appeal': [r'appeal', r'complain', r'report', r'create', r'new'],
            'check_status': [r'status', r'check', r'progress', r'update'],
            'provide_info': [r'provide', r'here', r'attached', r'additional'],
            'escalate': [r'escalate', r'urgent', r'critical', r'manager'],
            'close_appeal': [r'close', r'done', r'resolve', r'finish'],
            'get_help': [r'help', r'guide', r'how', r'assist'],
            'cancel': [r'cancel', r'never mind', r'discard', r'exit']
        }

        detected_intent = 'unknown'
        confidence = 0.0

        for intent, patterns in intent_patterns.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, content_lower))
            if matches > 0:
                confidence = matches / len(patterns)
                if confidence > 0.3:
                    detected_intent = intent
                    break

        parameters = self._extract_parameters(message_content, detected_intent)

        return detected_intent, parameters

    def _extract_parameters(self, message_content: str, intent: str) -> Dict:
        """
        Extract parameters from message based on intent
        
        Args:
            message_content: Message text
            intent: Detected intent
            
        Returns:
            Dictionary of extracted parameters
        """
        params = {}

        # Extract email if present
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, message_content)
        if emails:
            params['email'] = emails[0]

        # Extract phone numbers
        phone_pattern = r'\b(?:\+62|0)[0-9]{9,}\b'
        phones = re.findall(phone_pattern, message_content)
        if phones:
            params['phone'] = phones[0]

        # Extract category keywords
        categories = ['account', 'billing', 'technical', 'service', 'other']
        for category in categories:
            if category in message_content.lower():
                params['category'] = category
                break

        # Extract priority
        if any(word in message_content.lower() for word in ['urgent', 'critical', 'high']):
            params['priority'] = 'high'
        elif any(word in message_content.lower() for word in ['low', 'whenever']):
            params['priority'] = 'low'
        else:
            params['priority'] = 'normal'

        return params

    def queue_message(self, message: Dict) -> None:
        """Queue message for processing"""
        self.message_queue.append(message)
        logger.info(f"Message queued: {message.get('message_id')}")

    def dequeue_and_process(self) -> Optional[Dict]:
        """Dequeue and process next message"""
        if not self.message_queue:
            return None

        message = self.message_queue.pop(0)
        message['processed'] = True
        self.processed_messages.append(message)
        logger.info(f"Message processed: {message.get('message_id')}")
        return message


class AppealManager:
    """Manages appeal creation, updates, and retrieval"""

    def __init__(self):
        self.appeals: Dict[str, Appeal] = {}
        self.user_appeals: Dict[str, List[str]] = {}

    def create_appeal(self, user_id: str, category: str, subject: str, 
                     description: str, priority: str = "normal") -> Appeal:
        """
        Create new appeal
        
        Args:
            user_id: User ID
            category: Appeal category
            subject: Appeal subject
            description: Appeal description
            priority: Appeal priority level
            
        Returns:
            Created Appeal object
        """
        try:
            appeal_id = self._generate_appeal_id()
            appeal = Appeal(
                appeal_id=appeal_id,
                user_id=user_id,
                category=category,
                subject=subject,
                description=description,
                priority=priority
            )

            self.appeals[appeal_id] = appeal

            if user_id not in self.user_appeals:
                self.user_appeals[user_id] = []
            self.user_appeals[user_id].append(appeal_id)

            logger.info(f"Appeal created: {appeal_id} for user {user_id}")
            return appeal

        except Exception as e:
            logger.error(f"Error creating appeal: {str(e)}")
            return None

    def update_appeal_status(self, appeal_id: str, status: AppealStatus, 
                            notes: str = None) -> bool:
        """
        Update appeal status
        
        Args:
            appeal_id: Appeal ID
            status: New status
            notes: Optional notes
            
        Returns:
            Success status
        """
        try:
            if appeal_id not in self.appeals:
                logger.warning(f"Appeal not found: {appeal_id}")
                return False

            appeal = self.appeals[appeal_id]
            appeal.status = status
            appeal.updated_at = datetime.utcnow().isoformat()

            if notes:
                appeal.notes.append({
                    'timestamp': appeal.updated_at,
                    'content': notes
                })

            logger.info(f"Appeal {appeal_id} status updated to {status.value}")
            return True

        except Exception as e:
            logger.error(f"Error updating appeal status: {str(e)}")
            return False

    def get_appeal(self, appeal_id: str) -> Optional[Appeal]:
        """Retrieve appeal by ID"""
        return self.appeals.get(appeal_id)

    def get_user_appeals(self, user_id: str) -> List[Appeal]:
        """Retrieve all appeals for a user"""
        appeal_ids = self.user_appeals.get(user_id, [])
        return [self.appeals[aid] for aid in appeal_ids if aid in self.appeals]

    def add_attachment(self, appeal_id: str, attachment_url: str) -> bool:
        """Add attachment to appeal"""
        try:
            if appeal_id not in self.appeals:
                return False

            self.appeals[appeal_id].attachments.append(attachment_url)
            self.appeals[appeal_id].updated_at = datetime.utcnow().isoformat()
            logger.info(f"Attachment added to appeal {appeal_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding attachment: {str(e)}")
            return False

    def escalate_appeal(self, appeal_id: str, reason: str) -> bool:
        """Escalate appeal to higher priority"""
        try:
            if appeal_id not in self.appeals:
                return False

            appeal = self.appeals[appeal_id]
            appeal.status = AppealStatus.ESCALATED
            appeal.priority = "high"
            appeal.updated_at = datetime.utcnow().isoformat()
            appeal.notes.append({
                'timestamp': appeal.updated_at,
                'content': f"Escalated: {reason}"
            })

            logger.info(f"Appeal {appeal_id} escalated")
            return True

        except Exception as e:
            logger.error(f"Error escalating appeal: {str(e)}")
            return False

    def close_appeal(self, appeal_id: str, resolution: str) -> bool:
        """Close appeal with resolution"""
        try:
            if appeal_id not in self.appeals:
                return False

            appeal = self.appeals[appeal_id]
            appeal.status = AppealStatus.CLOSED
            appeal.resolution = resolution
            appeal.updated_at = datetime.utcnow().isoformat()

            logger.info(f"Appeal {appeal_id} closed with resolution")
            return True

        except Exception as e:
            logger.error(f"Error closing appeal: {str(e)}")
            return False

    def _generate_appeal_id(self) -> str:
        """Generate unique appeal ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        count = len(self.appeals) + 1
        return f"APP-{timestamp}-{count:04d}"


class ResponseGenerator:
    """Generates appropriate bot responses"""

    # Response templates
    TEMPLATES = {
        'welcome': "Selamat datang di Bot Appeal kami! 👋\n\nSaya siap membantu Anda dengan:\n• Membuat appeal baru\n• Cek status appeal\n• Eskalasi kasus\n\nAda yang bisa saya bantu?",
        'help': "📋 Cara Menggunakan Bot Appeal:\n\n1️⃣ Ketik 'appeal' untuk buat appeal baru\n2️⃣ Ketik 'status' untuk cek status appeal\n3️⃣ Kirim dokumen/foto untuk lampiran\n4️⃣ Ketik 'escalate' jika urgent\n\nBagaimana?",
        'appeal_created': "✅ Appeal berhasil dibuat!\n\n📌 ID Appeal: {appeal_id}\n📁 Kategori: {category}\n⏰ Status: {status}\n\nTim kami akan meninjau dalam 24 jam.",
        'status_check': "📊 Status Appeal Anda:\n\n📌 ID: {appeal_id}\n📁 Kategori: {category}\n⏰ Status: {status}\n🔄 Diperbarui: {updated_at}",
        'invalid_input': "❌ Input tidak valid. Mohon ulangi atau ketik 'help' untuk panduan.",
        'error': "⚠️ Terjadi kesalahan. Silakan coba lagi.",
    }

    @staticmethod
    def generate_response(response_type: str, **kwargs) -> str:
        """
        Generate response based on type and parameters
        
        Args:
            response_type: Type of response
            **kwargs: Additional parameters for template
            
        Returns:
            Formatted response string
        """
        template = ResponseGenerator.TEMPLATES.get(response_type, ResponseGenerator.TEMPLATES['error'])
        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    @staticmethod
    def generate_menu_response() -> str:
        """Generate menu response with options"""
        return "📱 Pilih opsi:\n\n1️⃣ Buat Appeal Baru\n2️⃣ Cek Status Appeal\n3️⃣ Bantuan\n4️⃣ Hubungi Admin\n\nBalas dengan angka (1-4)"


class ConversationState:
    """Manages conversation state for each user"""

    def __init__(self):
        self.states: Dict[str, Dict] = {}

    def initialize_state(self, user_id: str) -> None:
        """Initialize conversation state for user"""
        self.states[user_id] = {
            'current_step': 'menu',
            'appeal_draft': {},
            'last_action': datetime.utcnow().isoformat(),
            'conversation_history': []
        }

    def get_state(self, user_id: str) -> Dict:
        """Get conversation state for user"""
        if user_id not in self.states:
            self.initialize_state(user_id)
        return self.states[user_id]

    def update_state(self, user_id: str, step: str, data: Dict = None) -> None:
        """Update conversation state"""
        if user_id not in self.states:
            self.initialize_state(user_id)

        state = self.states[user_id]
        state['current_step'] = step
        state['last_action'] = datetime.utcnow().isoformat()

        if data:
            state['appeal_draft'].update(data)

    def add_to_history(self, user_id: str, message: str, sender: str = 'user') -> None:
        """Add message to conversation history"""
        if user_id not in self.states:
            self.initialize_state(user_id)

        self.states[user_id]['conversation_history'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'sender': sender,
            'message': message
        })

    def get_appeal_draft(self, user_id: str) -> Dict:
        """Get appeal draft for user"""
        return self.get_state(user_id).get('appeal_draft', {})

    def clear_state(self, user_id: str) -> None:
        """Clear conversation state for user"""
        if user_id in self.states:
            del self.states[user_id]


class BotEngine:
    """Main bot engine that orchestrates all components"""

    def __init__(self):
        self.message_handler = MessageHandler()
        self.appeal_manager = AppealManager()
        self.conversation_state = ConversationState()
        self.user_profiles: Dict[str, UserProfile] = {}

    def process_message(self, raw_message: Dict) -> Optional[str]:
        """
        Process incoming message and generate response
        
        Args:
            raw_message: Raw message from WhatsApp
            
        Returns:
            Response message string
        """
        try:
            # Parse message
            parsed_msg = self.message_handler.parse_message(raw_message)
            if not parsed_msg:
                return ResponseGenerator.generate_response('error')

            user_id = parsed_msg['from_number']
            message_content = parsed_msg['content']

            # Initialize user if new
            if user_id not in self.user_profiles:
                self._initialize_user(user_id)

            # Update last interaction
            self.user_profiles[user_id].last_interaction = datetime.utcnow().isoformat()

            # Extract intent
            intent, parameters = self.message_handler.extract_intent(message_content)

            # Get conversation state
            state = self.conversation_state.get_state(user_id)

            # Add to history
            self.conversation_state.add_to_history(user_id, message_content, 'user')

            # Route to appropriate handler
            response = self._route_intent(user_id, intent, message_content, parameters)

            # Add bot response to history
            self.conversation_state.add_to_history(user_id, response, 'bot')

            logger.info(f"Message processed for user {user_id}: intent={intent}")
            return response

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return ResponseGenerator.generate_response('error')

    def _initialize_user(self, user_id: str) -> None:
        """Initialize new user profile"""
        self.user_profiles[user_id] = UserProfile(
            user_id=user_id,
            phone_number=user_id,
            name=f"User_{user_id[-4:]}"
        )
        self.conversation_state.initialize_state(user_id)

    def _route_intent(self, user_id: str, intent: str, message: str, 
                     parameters: Dict) -> str:
        """Route intent to appropriate handler"""
        handlers = {
            'create_appeal': self._handle_create_appeal,
            'check_status': self._handle_check_status,
            'provide_info': self._handle_provide_info,
            'escalate': self._handle_escalate,
            'close_appeal': self._handle_close_appeal,
            'get_help': self._handle_get_help,
            'cancel': self._handle_cancel,
        }

        handler = handlers.get(intent, self._handle_unknown)
        return handler(user_id, message, parameters)

    def _handle_create_appeal(self, user_id: str, message: str, params: Dict) -> str:
        """Handle appeal creation"""
        draft = self.conversation_state.get_appeal_draft(user_id)

        # Collect required information
        if 'category' not in draft:
            return "📁 Kategori apa? (account/billing/technical/service/other)"

        if 'subject' not in draft:
            self.conversation_state.update_state(user_id, 'collecting_subject',
                                                 {'category': params.get('category', 'other')})
            return "📝 Judul/subject appeal?"

        if 'description' not in draft:
            self.conversation_state.update_state(user_id, 'collecting_description',
                                                 {'subject': message})
            return "📄 Jelaskan detail masalah Anda:"

        # Create appeal
        draft.update(params)
        appeal = self.appeal_manager.create_appeal(
            user_id=user_id,
            category=draft.get('category', 'other'),
            subject=draft.get('subject', message),
            description=draft.get('description', message),
            priority=draft.get('priority', 'normal')
        )

        if appeal:
            self.conversation_state.clear_state(user_id)
            self.user_profiles[user_id].total_appeals += 1
            return ResponseGenerator.generate_response(
                'appeal_created',
                appeal_id=appeal.appeal_id,
                category=appeal.category,
                status=appeal.status.value
            )

        return ResponseGenerator.generate_response('error')

    def _handle_check_status(self, user_id: str, message: str, params: Dict) -> str:
        """Handle status check"""
        appeals = self.appeal_manager.get_user_appeals(user_id)

        if not appeals:
            return "📭 Anda belum membuat appeal apapun."

        if len(appeals) == 1:
            appeal = appeals[0]
            return ResponseGenerator.generate_response(
                'status_check',
                appeal_id=appeal.appeal_id,
                category=appeal.category,
                status=appeal.status.value,
                updated_at=appeal.updated_at[:10]
            )

        # Multiple appeals - show list
        response = "📊 Daftar Appeal Anda:\n\n"
        for i, appeal in enumerate(appeals, 1):
            response += f"{i}. {appeal.appeal_id} - {appeal.status.value}\n"
        response += "\nReply dengan nomor untuk detail"
        return response

    def _handle_provide_info(self, user_id: str, message: str, params: Dict) -> str:
        """Handle additional information/attachments"""
        appeals = self.appeal_manager.get_user_appeals(user_id)
        if not appeals:
            return "❌ Belum ada appeal yang aktif."

        latest_appeal = appeals[-1]
        self.appeal_manager.add_attachment(latest_appeal.appeal_id, message)
        return f"✅ Informasi/lampiran ditambahkan ke appeal {latest_appeal.appeal_id}"

    def _handle_escalate(self, user_id: str, message: str, params: Dict) -> str:
        """Handle escalation"""
        appeals = self.appeal_manager.get_user_appeals(user_id)
        if not appeals:
            return "❌ Belum ada appeal untuk dieskalasi."

        latest_appeal = appeals[-1]
        self.appeal_manager.escalate_appeal(
            latest_appeal.appeal_id,
            message or "User requested escalation"
        )
        return f"⚠️ Appeal {latest_appeal.appeal_id} telah dieskalasi ke tim senior."

    def _handle_close_appeal(self, user_id: str, message: str, params: Dict) -> str:
        """Handle appeal closure"""
        appeals = self.appeal_manager.get_user_appeals(user_id)
        if not appeals:
            return "❌ Belum ada appeal untuk ditutup."

        latest_appeal = appeals[-1]
        self.appeal_manager.close_appeal(latest_appeal.appeal_id, message or "Closed by user")
        return f"✅ Appeal {latest_appeal.appeal_id} telah ditutup."

    def _handle_get_help(self, user_id: str, message: str, params: Dict) -> str:
        """Handle help request"""
        return ResponseGenerator.generate_response('help')

    def _handle_cancel(self, user_id: str, message: str, params: Dict) -> str:
        """Handle cancellation"""
        self.conversation_state.clear_state(user_id)
        return "❌ Dibatalkan. Ketik apapun untuk mulai lagi."

    def _handle_unknown(self, user_id: str, message: str, params: Dict) -> str:
        """Handle unknown intent"""
        return ResponseGenerator.TEMPLATES['menu'] + "\n\n" + ResponseGenerator.generate_response('invalid_input')


# Initialization function
def initialize_bot() -> BotEngine:
    """Initialize and return bot engine"""
    bot = BotEngine()
    logger.info("WhatsApp Appeal Bot Part 2 initialized successfully")
    return bot


if __name__ == "__main__":
    # Example usage
    bot = initialize_bot()
    print("Bot initialized and ready for messages")
