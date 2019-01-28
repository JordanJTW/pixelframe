import pychromecast


class CastPlugin:
    def __init__(self):
        self._controller = None
        self._current_image_url = None
        self._instance = None

    def setup_plugin(self, instance, renderer):
        print('Setting up CastPlugin...')

        self._instance = instance
        self._add_listener()

    def _add_listener(self):
        self._controller = pychromecast.controllers.media.MediaController()
        self._controller.register_status_listener(self)

        for cast in pychromecast.get_chromecasts():
            print('Adding listener: %s' % (cast.device.friendly_name))
            cast.register_handler(self._controller)

    def new_media_status(self, status):
        image_size = None
        image_url = None

        for image in status.images:
            if not image.height and not image.width:
                image_url = image.url
                break

            size = image.height * image.width

            if (not image_size or size < image_size) and image.url:
                image_size = size
                image_url = image.url

        if image_url and self._current_image_url != image_url:
            print('Update to:', image_url)
            self._current_image_url = image_url
            self._instance.set_background_url(image_url)

    def update(self):
        pass
