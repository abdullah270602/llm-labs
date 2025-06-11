from http.client import HTTPException
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.requests import Request

config = Config('.env') #TODO Load with os.getenv
oauth = OAuth(config)

oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

async def get_google_user_info(request: Request):
    token = await oauth.google.authorize_access_token(request)

    if 'userinfo' not in token:
        raise HTTPException(status_code=400, detail="User info not available in token.")
    
    user_info = token['userinfo']
    return user_info
