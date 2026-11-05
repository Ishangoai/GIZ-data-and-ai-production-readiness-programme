"""Image Editor: a Gradio app to upload and edit an image.

The module only exposes ``build_app`` so that ``api/main.py`` can mount the
interface on the FastAPI server. Running this file directly still works, which
makes local testing faster than starting the whole API.
"""

from dataclasses import dataclass

import gradio as gr
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

FILTER_NONE = "None"
FILTER_SEPIA = "Sepia"
FILTER_INVERT = "Invert colors"
FILTER_BLUR = "Blur"
FILTER_SHARPEN = "Sharpen"
FILTER_OPTIONS = [
    FILTER_NONE,
    FILTER_SEPIA,
    FILTER_INVERT,
    FILTER_BLUR,
    FILTER_SHARPEN,
]

# 1.0 means "unchanged" for Pillow's enhancers, so the sliders start there.
DEFAULT_BRIGHTNESS = 1.0
DEFAULT_CONTRAST = 1.0
DEFAULT_ANGLE = 0
# Black shadows with warm wheat highlights give a classic sepia look.
# Pillow accepts plain color names, which are easier to read than hex codes.
SEPIA_DARK_TONE = "black"
SEPIA_LIGHT_TONE = "wheat"
BLUR_RADIUS = 3
# White blends in with most web pages better than the default black corners.
ROTATION_FILL_COLOR = "white"


@dataclass(frozen=True)
class EditSettings:
    """Every edit the user can request."""

    grayscale: bool = False
    brightness: float = DEFAULT_BRIGHTNESS
    contrast: float = DEFAULT_CONTRAST
    angle: float = DEFAULT_ANGLE
    flip_horizontal: bool = False
    flip_vertical: bool = False
    filter_name: str = FILTER_NONE


# --------------------------------------------------------------------------
# Image operations. Kept as pure functions (no Gradio objects) so they can
# be unit tested without starting a server.
# --------------------------------------------------------------------------
def apply_flips(
    image: Image.Image, flip_horizontal: bool, flip_vertical: bool
) -> Image.Image:
    """Mirror the image horizontally and/or vertically."""
    if flip_horizontal:
        image = ImageOps.mirror(image)
    if flip_vertical:
        image = ImageOps.flip(image)
    return image


def to_grayscale(image: Image.Image) -> Image.Image:
    """Convert to grayscale but keep three channels for later steps."""
    # Going back to RGB is deliberate: filters such as sepia expect the same
    # image mode regardless of whether grayscale was switched on.
    return image.convert("L").convert("RGB")


def apply_filter(image: Image.Image, filter_name: str) -> Image.Image:
    """Apply one of the named creative filters."""
    if filter_name == FILTER_SEPIA:
        # Sepia is a tint of a grayscale image, so grayscale it first.
        gray = ImageOps.grayscale(image)
        return ImageOps.colorize(gray, SEPIA_DARK_TONE, SEPIA_LIGHT_TONE)
    if filter_name == FILTER_INVERT:
        return ImageOps.invert(image)
    if filter_name == FILTER_BLUR:
        return image.filter(ImageFilter.GaussianBlur(BLUR_RADIUS))
    if filter_name == FILTER_SHARPEN:
        return image.filter(ImageFilter.SHARPEN)
    return image


def adjust_brightness_and_contrast(
    image: Image.Image, brightness: float, contrast: float
) -> Image.Image:
    """Scale brightness and contrast (1.0 means unchanged)."""
    image = ImageEnhance.Brightness(image).enhance(brightness)
    return ImageEnhance.Contrast(image).enhance(contrast)


def rotate(image: Image.Image, angle: float) -> Image.Image:
    """Rotate counter-clockwise, growing the canvas so nothing is cut."""
    # expand=True stops the corners being cropped on diagonal angles, which
    # users would otherwise read as the app losing part of their photo.
    return image.rotate(angle, expand=True, fillcolor=ROTATION_FILL_COLOR)


def apply_edits(image: Image.Image, settings: EditSettings) -> Image.Image:
    """Apply every selected edit to a copy of the image."""
    # Converting to RGB first guarantees every later step sees the same
    # mode. Uploads can be RGBA, palette based or grayscale, and some
    # Pillow operations (such as invert) fail on RGBA.
    result = image.convert("RGB")
    result = apply_flips(
        result, settings.flip_horizontal, settings.flip_vertical
    )
    if settings.grayscale:
        result = to_grayscale(result)
    result = apply_filter(result, settings.filter_name)
    result = adjust_brightness_and_contrast(
        result, settings.brightness, settings.contrast
    )
    # Rotation runs last so earlier steps work on the original pixel grid.
    return rotate(result, settings.angle)


# --------------------------------------------------------------------------
# Event handlers
# --------------------------------------------------------------------------
def edit_image(
    image: Image.Image | None,
    grayscale: bool,
    brightness: float,
    contrast: float,
    angle: float,
    flip_horizontal: bool,
    flip_vertical: bool,
    filter_name: str,
) -> Image.Image | None:
    """Gradio handler: edit the uploaded image using the control values."""
    # The handler also fires when the user removes the image, so None must
    # be handled to clear the output rather than raise an error.
    if image is None:
        return None
    # Packing the values into a dataclass keeps the pure functions free of
    # long argument lists and Gradio specifics.
    settings = EditSettings(
        grayscale=grayscale,
        brightness=brightness,
        contrast=contrast,
        angle=angle,
        flip_horizontal=flip_horizontal,
        flip_vertical=flip_vertical,
        filter_name=filter_name,
    )
    return apply_edits(image, settings)


def reset_controls() -> tuple[bool, float, float, float, bool, bool, str]:
    """Return the default value of every control."""
    # Reading the defaults from EditSettings keeps one source of truth, so
    # the reset button can never drift from the real defaults.
    defaults = EditSettings()
    return (
        defaults.grayscale,
        defaults.brightness,
        defaults.contrast,
        defaults.angle,
        defaults.flip_horizontal,
        defaults.flip_vertical,
        defaults.filter_name,
    )


def describe_image(image: Image.Image | None) -> str:
    """Return a short size description of the uploaded image."""
    if image is None:
        return "Upload an image to get started."
    width, height = image.size
    return f"Original size: **{width} x {height} px**"


# --------------------------------------------------------------------------
# User interface
# --------------------------------------------------------------------------
def build_app() -> gr.Blocks:
    """Create the Gradio interface and wire up its events."""
    # Building inside a function (not at import time) means importing this
    # module in api/main.py has no side effects until the app is needed.
    with gr.Blocks(title="Image Editor") as app:
        gr.Markdown("# Image Editor\nUpload an image and adjust the controls.")

        with gr.Row():
            with gr.Column():
                # type="pil" hands us a Pillow image, which is what all the
                # editing functions work with.
                input_image = gr.Image(
                    label="Original image", type="pil", sources=["upload"]
                )
                image_info = gr.Markdown(describe_image(None))

                grayscale_box = gr.Checkbox(label="Grayscale")
                brightness_slider = gr.Slider(
                    0.5, 1.5, value=DEFAULT_BRIGHTNESS, step=0.05,
                    label="Brightness",
                )
                contrast_slider = gr.Slider(
                    0.5, 1.5, value=DEFAULT_CONTRAST, step=0.05,
                    label="Contrast",
                )
                angle_slider = gr.Slider(
                    -180, 180, value=DEFAULT_ANGLE, step=1,
                    label="Rotate (degrees)",
                )
                with gr.Row():
                    flip_horizontal_box = gr.Checkbox(label="Flip horizontal")
                    flip_vertical_box = gr.Checkbox(label="Flip vertical")
                filter_dropdown = gr.Dropdown(
                    choices=FILTER_OPTIONS, value=FILTER_NONE, label="Filter"
                )
                reset_button = gr.Button("Reset", variant="stop")

            with gr.Column():
                # The built-in download button saves exactly what is shown,
                # so we do not need to write a separate export function.
                # PNG avoids re-compression artefacts on the saved file.
                output_image = gr.Image(
                    label="Edited image",
                    type="pil",
                    format="png",
                    interactive=False,
                    buttons=["download", "fullscreen"],
                )

        controls = [
            grayscale_box,
            brightness_slider,
            contrast_slider,
            angle_slider,
            flip_horizontal_box,
            flip_vertical_box,
            filter_dropdown,
        ]

        # triggers=None re-runs the function whenever any input changes, so
        # the preview is live without wiring every control separately.
        gr.on(
            triggers=None,
            fn=edit_image,
            inputs=[input_image, *controls],
            outputs=output_image,
        )
        input_image.change(describe_image, input_image, image_info)
        # Resetting the controls fires their change events, which redraw
        # the original image in the output for us.
        reset_button.click(reset_controls, outputs=controls)

    return app


if __name__ == "__main__":
    # Only runs for quick local testing. In production, api/main.py mounts
    # the app and the server is started by uvicorn.
    build_app().launch(theme=gr.themes.Soft())