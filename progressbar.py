import traitlets
from traitlets import Unicode
from ipywidgets import IntProgress

class ProgressWithTitle(IntProgress):

    title = Unicode()

    @traitlets.observe('value', 'max', 'title')
    def _update_description(self, change):
        self.description = '{} ({}/{})'.format(self.title, self.value, self.max)
