import logging
import uvicorn
import asyncio
import subprocess
import os
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from src.main import instasea, config_dict
from src.core.paths import mqtt_file
from src.services.instagram import IgClient
from src.services.validator import create_message_model, Message
from src.services.tickets import TicketsManager


@dataclass
class QueueManager:
    tickets: TicketsManager
    q: asyncio.Queue
    q_cache: set[int] = field(default_factory=set)

    async def process(self) -> None:
        while True:
            thread_id: int = await self.q.get()
            logging.info(f"Processing message from thread with ID: {thread_id}")
            await asyncio.to_thread(self.tickets.create_ticket, thread_id)
            self.q_cache.discard(thread_id)
            logging.info(f"Operations in thread with ID: {thread_id} finished")
            self.q.task_done()

    async def validate(self, raw_notification: dict) -> None:
        message: Message | bool = create_message_model(raw_notification)
        if message:
            if message.thread_id not in self.q_cache:
                self.q_cache.add(message.thread_id)
                await self.q.put(message.thread_id)
            else:
                logging.info(f"Ignoring message from {message.username} as already in queue")



@instasea.command(help="Real-life chatting.")
def chat():
    uvicorn.run(app, host="127.0.0.1", port=8000)


def authenticate(ig_client: IgClient) -> bool:
    try:
        ig_client.call_api("authenticate", ig_client.credentials)
        return True
    except RuntimeError as e:
        logging.error(f"Instagrapi error: {type(e).__name__}. More info: {e}")
        return False


def start_listening() -> subprocess.Popen:  
    with open(os.devnull, 'w') as devnull:
        process = subprocess.Popen(
            ["node", str(mqtt_file)],  
            stdout=devnull,
            stderr=devnull,
        )
    logging.info(f"Started MQTT listener [{process.pid}]")
    return process


@asynccontextmanager
async def lifespan(app: FastAPI):
    tickets = TicketsManager(config=config_dict["config"])
    queue = QueueManager(tickets=tickets, q=asyncio.Queue())
    app.state.manager = queue
    
    if authenticate(tickets.config.ig_client):
        mqtt_process = start_listening()  
        app.state.mqtt_process = mqtt_process  
        worker_task = asyncio.create_task(queue.process())
        yield 
        worker_task.cancel()
        await asyncio.to_thread(mqtt_process.terminate)
        logging.info(f"Terminated MQTT process [{mqtt_process.pid}]")


app = FastAPI(lifespan=lifespan)


def get_manager() -> QueueManager:
    return app.state.manager


@app.post("/notifications")
async def new_notification(raw_notification: dict, manager: QueueManager = Depends(get_manager)):
    asyncio.create_task(manager.validate(raw_notification.get("notification")))