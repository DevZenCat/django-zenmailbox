try:
    from django.conf import settings
    if "ckeditor" not in getattr(settings, "INSTALLED_APPS", []):
        raise ImportError
    from ckeditor.widgets import CKEditorWidget

    ZENMAILBOX_CKEDITOR_SETTINGS = getattr(settings, "ZENMAILBOX_CKEDITOR_SETTINGS", {})

    class HtmlWidget(CKEditorWidget):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs, **ZENMAILBOX_CKEDITOR_SETTINGS)
except ImportError:
    from django.contrib.admin.widgets import AdminTextareaWidget
    HtmlWidget = AdminTextareaWidget
