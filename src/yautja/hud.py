"""Independent HUD softness and opacity, applied before scene composition."""
import math

from PIL import Image, ImageChops, ImageFilter

from .colors import HUD_DEFAULTS

BLUR_ELEMENTS = tuple(key for key in HUD_DEFAULTS if key != 'target-flash')
OPACITY_ELEMENTS = tuple(HUD_DEFAULTS)


def element_values(amount, elements, keys, flag, upper):
    if not math.isfinite(amount) or not 0 <= amount <= upper:
        raise ValueError(f'--{flag} must be finite and between 0 and {upper}')
    result = dict.fromkeys(keys, float(amount))
    seen = set()
    if elements is not None:
        for entry in elements.split(','):
            key, separator, value = entry.partition('=')
            key = key.strip()
            if not separator or key not in result:
                raise ValueError(f'--{flag}-elements needs element=value assignments; choose ' + ', '.join(result))
            if key in seen:
                raise ValueError(f'Duplicate {flag} element: ' + key)
            seen.add(key)
            try:
                value = float(value)
            except ValueError:
                raise ValueError(f'{flag} value must be a number: ' + key) from None
            if not math.isfinite(value) or not 0 <= value <= upper:
                raise ValueError(f'{flag} value must be finite and between 0 and {upper}: ' + key)
            result[key] = value
    return result, seen


def hud_blurs(amount=0., elements=None):
    """Resolve the shared radius and explicit element overrides, in reference px."""
    return element_values(amount, elements, BLUR_ELEMENTS, 'hud-blur', 20)[0]


def hud_opacities(amount=1., elements=None):
    """A target override also controls its flash unless flash is set explicitly."""
    result, seen = element_values(amount, elements, OPACITY_ELEMENTS, 'hud-opacity', 1)
    if 'target-flash' not in seen:
        result['target-flash'] = result['target']
    return result


def blur_layer(image, radius):
    if not radius:
        return image
    # Premultiplication avoids a dark fringe around translucent colored ink.
    mode = image.mode
    working = image.convert('RGBa') if mode == 'RGBA' else image
    return working.filter(ImageFilter.GaussianBlur(radius)).convert(mode)


def opacity_layer(image, amount):
    if amount == 1:
        return image
    if amount == 0:
        return Image.new(image.mode, image.size)
    if image.mode == 'RGBA':
        result = image.copy()
        result.putalpha(image.getchannel('A').point(lambda a: round(a * amount)))
        return result
    # Screen-blended artwork uses black as transparency, so scale its light.
    return image.point(lambda value: round(value * amount))


class HudPanel:
    """Keep the original canvas unless elements need separate appearance controls."""
    def __init__(self, mode, size, radii, elements, opacities, *, separate=False):
        self.mode, self.size = mode, size
        self.radii = {key: radii[key] for key in elements}
        self.opacities = {key: opacities[key] for key in elements}
        self.separate = separate or any(self.radii.values()) or any(value != 1 for value in self.opacities.values())
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
            layer = opacity_layer(layer, self.opacities[key])
            result = Image.alpha_composite(result, layer) if self.mode == 'RGBA' else ImageChops.screen(result, layer)
        return result, pad
