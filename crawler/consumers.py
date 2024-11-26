import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TaskProgressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        
        # Join group
        await self.channel_layer.group_add(
            f"task_{self.task_id}",
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            f"task_{self.task_id}",
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to group
        await self.channel_layer.group_send(
            f"task_{self.task_id}",
            {
                'type': 'task_progress',
                'message': message
            }
        )

    async def task_progress(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
