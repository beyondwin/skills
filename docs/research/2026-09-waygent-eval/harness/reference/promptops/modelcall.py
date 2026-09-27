from .fake_model import ModelError
from .retry import retry_async


async def restyle(model, body, style, model_name):
    return await retry_async(lambda: model.restyle(body, style, model_name), attempts=3, retry_on=(ModelError,))
