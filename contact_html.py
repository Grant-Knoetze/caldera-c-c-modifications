import json

from aiohttp_jinja2 import template

from app.utility.base_world import BaseWorld

import rc4
import base64


class Contact(BaseWorld):

    def __init__(self, services):
        self.name = 'html'
        self.description = 'Accept beacons through an HTML page'
        self.app_svc = services.get('app_svc')
        self.contact_svc = services.get('contact_svc')

    async def start(self):
        self.app_svc.application.router.add_route('*', self.get_config('app.contact.html'), self._accept_beacon)

    """ PRIVATE """

    @template('weather.html')
    async def _accept_beacon(self, request):
        try:

            fulldmsg = await request.text()
            #Data Sent through POST parameters
            length = len("page=download.html&file=weather.html&apitoken=")
            encodedmsg = fulldmsg[length:]
            print("Encoded Message: %s\n" % encodedmsg)
            #decode & decrypt the message (latin1 is the only option for decoding as it is without any errors or issues)
            encryptedmsg = base64.b64decode(encodedmsg).decode('latin1')
            json_msg = rc4.rc4(encryptedmsg, "RedTeam")    #RC4 decryption
            profile = json.loads(json_msg)
            profile['paw'] = profile.get('paw')
            profile['contact'] = 'html'
            agent, instructions = await self.contact_svc.handle_heartbeat(**profile)
            response = dict(paw=agent.paw,
                            sleep=await agent.calculate_sleep(),
                            watchdog=agent.watchdog,
                            instructions=json.dumps([json.dumps(i.display) for i in instructions]))
            response_json = json.dumps(response)
            encrypted_msg = rc4.rc4(response_json, "RedTeam")
            encoded_msg = base64.b64encode(bytes(encrypted_msg, "latin1")).decode("latin1")
            return dict(instructions=encoded_msg)
        except Exception:
            return dict(instructions=[])
