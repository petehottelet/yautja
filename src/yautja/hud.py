"""Independent HUD softness, applied to artwork before scene composition."""
import math

from PIL import Image, ImageChops, ImageFilter

from .colors import HUD_DEFAULTS

BLUR_ELEMENTS = tuple(key for key in HUD_DEFAULTS if key != 'target-flash')


def hud_blurs(amount=0., elements=None):
    """Resolve the shared radius and explicit element overrides, in reference px."""
    if not math.isfinite(amount) or not 0 <= amount <= 20:
        raise ValueError('--hud-blur must be finite and between 0 and 20')
    result = dict.fromkeys(BLUR_ELEMENTS, float(amount))
    seen = set()
    if elements is not None:
        for entry in elements.split(','):
            key, separator, value = entry.partition('=')
            key = key.strip()
            if not separator or key not in result:
                raise ValueError('--hud-blur-elements needs element=radius assignments; choose ' + ', '.join(result))
            if key in seen:
                raise ValueError('Duplicate HUD blur element: ' + key)
            seen.add(key)
            try:
                value = float(value)
            except ValueError:
                raise ValueError('HUD blur radius must be a number: ' + key) from None
            if not math.isfinite(value) or not 0 <= value <= 20:
                raise ValueError('HUD blur radius must be finite and between 0 and 20: ' + key)
            result[key] = value
    return result


def blur_layer(image, radius):
    if not radius:
        return image
    # Premultiplication avoids a dark fringe around translucent colored ink.
    mode = image.mode
    working = image.convert('RGBa') if mode == 'RGBA' else image
    return working.filter(ImageFilter.GaussianBlur(radius)).convert(mode)


class HudPanel:
    """Keep the original shared canvas when sharp; split only softened panels."""
    def __init__(self, mode, size, radii, elements):
        self.mode, self.size = mode, size
        self.radii = {key: radii[key] for key in elements}
        self.separate = any(self.radii.values())
        self.layers = {}

    def layer(self, element):
        key = element if self.separate else 'shared'
        if key not in self.layers:
            self.layers[key] = Image.new(self.mode, self.size)
        return self.layers[key]

    def replace(self, element, image):
        self.layers[element if self.separate else 'shared'] = image

    def finish(self):
        if not self.separate:
            return self.layers['shared'], 0
        # Reserve room for diffusion beyond panel bounds; clip at the frame only.
        pad = math.ceil(3 * max(self.radii.values()))
        size = (self.size[0] + 2 * pad, self.size[1] + 2 * pad)
        result = Image.new(self.mode, size)
        for key, artwork in self.layers.items():
            layer = Image.new(self.mode, size)
            layer.paste(artwork, (pad, pad))
            layer = blur_layer(layer, self.radii[key])
            result = Image.alpha_composite(result, layer) if self.mode == 'RGBA' else ImageChops.screen(result, layer)
        return result, pad
