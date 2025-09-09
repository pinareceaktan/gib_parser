# gib_parser/core/page_handlers/factory.py



from gib_parser.helpers.abstract_classes import AbstractPageHandlerFactory, AbstractPageHandler

# from gib_parser.core.page_handlers.internal_circulars import InternalCircularsHandler
# from gib_parser.core.page_handlers.regulations import RegulationsHandler
from gib_parser.core.page_handlers.law_matters import LawMattersHandler
from gib_parser.core.page_handlers.law_justifications import LawJustificationHandler
from gib_parser.core.page_handlers.presidential_decree import PresidentialDecreeHandler
from gib_parser.core.page_handlers.ministerial_decree import MinisterialDecreeHandler
from gib_parser.core.page_handlers.regulations import RegulationsHandler
from gib_parser.core.page_handlers.notices import NoticesHandler
from gib_parser.core.page_handlers.internal_circulars import InternalCircularsHandler
from gib_parser.core.page_handlers.official_letters import OfficialLettersHandler
from gib_parser.core.page_handlers.circulars import CircularHandler
from gib_parser.core.page_handlers.private_rulings import PrivateRulingsHandler


from gib_parser import get_logger

base_logger = get_logger(__name__)

class PageHandlerFactory(AbstractPageHandlerFactory):
    def __init__(self, selenium_client, component_manager):
        super().__init__(selenium_client, component_manager)

        self._registry  = {
            "maddeler": LawMattersHandler(),
            "gerekçeler": LawJustificationHandler(),
            "cumhurbaşkani_kararlari":PresidentialDecreeHandler(),
            "b.k.k.":MinisterialDecreeHandler(),
            "yönetmelikler": RegulationsHandler(),
            "tebliğler": NoticesHandler(),
            "iç_genelgeler": InternalCircularsHandler(),
            "genel_yazılar": OfficialLettersHandler(),
            "sirküler": CircularHandler(),
            "özelgeler": PrivateRulingsHandler()

        }

    def get_handler(self, section_name: str):
        handler_cls = self._registry.get(section_name.lower())
        if handler_cls:
            return handler_cls
        else:
            base_logger.info(f"No handler found for section {section_name}")
            return None
