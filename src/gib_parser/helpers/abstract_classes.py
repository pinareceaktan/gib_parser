from abc import ABC, abstractmethod


class AbstractParsingClient(ABC):
    def __init__(self):
        pass


    @abstractmethod
    def make_driver_wait(self):
        pass

    @abstractmethod
    def make_driver_wait_for_a_text(self, outer_component, inner_component, min_cards, timeout):
        pass

    @abstractmethod
    def find_and_select_single_element(self, by, component_id):
        pass

    @staticmethod
    @abstractmethod
    def get_single_element_options(component):
        pass

    @abstractmethod
    def find_elements(self, by, component_id):
        pass

    @staticmethod
    @abstractmethod
    def click_component(component):
        pass

    @abstractmethod
    def select_component(self):
        pass

    @abstractmethod
    def find_element(self, by, component_id):
        pass

    @abstractmethod
    def go_to_page(self, page_num, timeout=10):
        pass


class AbstractComponentManager(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def get_component_id_by_tag(self, tag):
        pass

    @abstractmethod
    def get_all_tags(self) :
        pass


class AbstractPageHandlerFactory(ABC):
    def __init__(self, client, component_manager):
        self.client = client
        self.component_manager = component_manager



class AbstractPageHandler(ABC):
    def __init__(self):
        pass
    @abstractmethod
    def handle(self,
               parser:AbstractParsingClient,
               component_manager:AbstractComponentManager,
               law_name: str,
               section_name: str,
               sections_folder: str,
               laws_folder: str):
        """Each handler will override this"""
        pass