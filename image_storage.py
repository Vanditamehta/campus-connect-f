
import os
import uuid

import cloudinary
import cloudinary.uploader
from cloudinary import CloudinaryImage

from flask import current_app


CLOUDINARY_PREFIX = "cloudinary:"

ALLOWED_CLOUDINARY_ENV_VARS = (
    "CLOUDINARY_CLOUD_NAME",
    "CLOUDINARY_API_KEY",
    "CLOUDINARY_API_SECRET"
)


def configure_cloudinary():
    """Configure Cloudinary using environment variables."""

    values = {
        key: os.environ.get(key)
        for key in ALLOWED_CLOUDINARY_ENV_VARS
    }

    configured = [bool(value) for value in values.values()]

    if not any(configured):
        return False

    if not all(configured):
        raise ValueError(
            "Cloudinary configuration is incomplete. "
            "Please configure all three Cloudinary environment variables."
        )

    cloudinary.config(
        cloud_name=values["CLOUDINARY_CLOUD_NAME"],
        api_key=values["CLOUDINARY_API_KEY"],
        api_secret=values["CLOUDINARY_API_SECRET"],
        secure=True
    )

    return True


def store_image(file, folder, extension):
    """Store an image in Cloudinary or local storage."""

    if configure_cloudinary():

        try:
            file.stream.seek(0)

            result = cloudinary.uploader.upload(
                file.stream,
                folder=f"campusconnect/{folder}",
                resource_type="image",
                public_id=uuid.uuid4().hex,
                overwrite=False
            )

            return CLOUDINARY_PREFIX + result["public_id"]

        except Exception as error:
            current_app.logger.exception(
                "Cloudinary image upload failed."
            )
            raise ValueError(
                "Could not upload the image. Please try again."
            ) from error

    filename = f"{uuid.uuid4().hex}{extension}"

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    file.stream.seek(0)
    file.save(os.path.join(upload_folder, filename))

    return filename


def get_image_url(stored_image):
    """Return a displayable URL for a local or Cloudinary image."""

    if not stored_image:
        return None

    if stored_image.startswith(CLOUDINARY_PREFIX):
        public_id = stored_image[len(CLOUDINARY_PREFIX):]

        if not public_id:
            return None

        return CloudinaryImage(public_id).build_url(secure=True)

    return "/static/uploads/" + stored_image


def delete_image(stored_image):
    """Delete an image from Cloudinary or local storage."""

    if not stored_image:
        return

    if stored_image.startswith(CLOUDINARY_PREFIX):
        public_id = stored_image[len(CLOUDINARY_PREFIX):]

        if public_id:
            try:
                configure_cloudinary()

                cloudinary.uploader.destroy(
                    public_id,
                    resource_type="image"
                )

            except Exception:
                current_app.logger.exception(
                    "Could not delete Cloudinary image: %s",
                    public_id
                )

        return

    upload_folder = os.path.abspath(
        current_app.config["UPLOAD_FOLDER"]
    )

    image_path = os.path.abspath(
        os.path.join(upload_folder, os.path.basename(stored_image))
    )

    if os.path.dirname(image_path) != upload_folder:
        return

    try:
        if os.path.isfile(image_path):
            os.remove(image_path)

    except OSError:
        current_app.logger.exception(
            "Could not delete local image: %s",
            stored_image
        )
