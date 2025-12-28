"""
FastAPI 애플리케이션을 위한 RabbitMQ 연결 및 메시징 유틸리티.
비동기 작업을 위해 aio-pika를 사용합니다.
"""

import asyncio
import json
from typing import Callable, Optional, Dict, Any
from contextlib import asynccontextmanager

import aio_pika
from aio_pika import Message, DeliveryMode, ExchangeType
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue, AbstractExchange



"""

RabbitMQ 모듈 기능 정리
RabbitMQClient 클래스
FastAPI 애플리케이션을 위한 비동기 RabbitMQ 클라이언트입니다.

연결 관리
connect() - RabbitMQ 서버 연결 수립
disconnect() - RabbitMQ 서버 연결 종료
is_connected - 연결 상태 확인 (프로퍼티)
큐 & 익스체인지 설정
declare_queue() - 큐 선언 (durable, auto_delete 옵션)
declare_exchange() - 익스체인지 선언 (DIRECT, FANOUT, TOPIC, HEADERS)
bind_queue() - 큐를 익스체인지에 바인딩
메시지 처리
publish() - 메시지 발행 (JSON 직렬화, 영속성 옵션, 헤더 지원)
consume() - 큐에서 메시지 소비 (콜백 기반, auto-ack 옵션)
유틸리티
get_channel() - 채널 컨텍스트 매니저 (자동 생명주기 관리)

"""


class RabbitMQClient:
    """
    FastAPI 애플리케이션을 위한 비동기 RabbitMQ 클라이언트.
    """

    def __init__(self, url: str, connection_name: str = "fastapi-service"):
        """
        RabbitMQ 클라이언트를 초기화합니다.
        
        Args:
            url: RabbitMQ 연결 URL (예: "amqp://user:pass@localhost:5672/")
            connection_name: 연결 이름 (모니터링에 유용)
        """
        self.url = url
        self.connection_name = connection_name
        self.connection: Optional[AbstractConnection] = None
        self.channel: Optional[AbstractChannel] = None
        self._is_connected = False

    async def connect(self) -> None:
        """RabbitMQ 서버에 연결을 수립합니다."""
        if self._is_connected:
            return

        self.connection = await aio_pika.connect_robust(
            self.url,
            client_properties={"connection_name": self.connection_name}
        )
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=10)
        self._is_connected = True

    async def disconnect(self) -> None:
        """RabbitMQ 서버 연결을 종료합니다."""
        if not self._is_connected:
            return

        if self.channel and not self.channel.is_closed:
            await self.channel.close()
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        
        self._is_connected = False
        self.channel = None
        self.connection = None

    async def declare_queue(
        self,
        queue_name: str,
        durable: bool = True,
        auto_delete: bool = False,
        arguments: Optional[Dict[str, Any]] = None
    ) -> AbstractQueue:
        """
        큐를 선언합니다.
        
        Args:
            queue_name: 큐 이름
            durable: 브로커 재시작 시에도 큐가 유지됨
            auto_delete: 마지막 소비자가 구독 해제 시 큐 삭제
            arguments: 추가 큐 인자
            
        Returns:
            AbstractQueue 인스턴스
        """
        if not self.channel:
            raise RuntimeError("채널이 초기화되지 않았습니다. 먼저 connect()를 호출하세요.")
        
        return await self.channel.declare_queue(
            queue_name,
            durable=durable,
            auto_delete=auto_delete,
            arguments=arguments
        )

    async def declare_exchange(
        self,
        exchange_name: str,
        exchange_type: ExchangeType = ExchangeType.DIRECT,
        durable: bool = True,
        auto_delete: bool = False
    ) -> AbstractExchange:
        """
        익스체인지를 선언합니다.
        
        Args:
            exchange_name: 익스체인지 이름
            exchange_type: 익스체인지 타입 (DIRECT, FANOUT, TOPIC, HEADERS)
            durable: 브로커 재시작 시에도 익스체인지가 유지됨
            auto_delete: 마지막 큐가 언바인드될 때 익스체인지 삭제
            
        Returns:
            AbstractExchange 인스턴스
        """
        if not self.channel:
            raise RuntimeError("채널이 초기화되지 않았습니다. 먼저 connect()를 호출하세요.")
        
        return await self.channel.declare_exchange(
            exchange_name,
            exchange_type,
            durable=durable,
            auto_delete=auto_delete
        )

    async def publish(
        self,
        message: Dict[str, Any],
        routing_key: str,
        exchange: str = "",
        persistent: bool = True,
        headers: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        익스체인지에 메시지를 발행합니다.
        
        Args:
            message: 메시지 페이로드 (JSON으로 직렬화됨)
            routing_key: 메시지 라우팅을 위한 라우팅 키
            exchange: 익스체인지 이름 (빈 문자열은 기본 익스체인지)
            persistent: 브로커 재시작 시에도 메시지가 유지됨
            headers: 선택적 메시지 헤더
        """
        if not self.channel:
            raise RuntimeError("채널이 초기화되지 않았습니다. 먼저 connect()를 호출하세요.")

        body = json.dumps(message).encode()
        
        aio_message = Message(
            body=body,
            delivery_mode=DeliveryMode.PERSISTENT if persistent else DeliveryMode.NOT_PERSISTENT,
            content_type="application/json",
            headers=headers or {}
        )

        if exchange:
            exchange_obj = await self.channel.get_exchange(exchange)
            await exchange_obj.publish(aio_message, routing_key=routing_key)
        else:
            await self.channel.default_exchange.publish(
                aio_message,
                routing_key=routing_key
            )

    async def consume(
        self,
        queue_name: str,
        callback: Callable,
        auto_ack: bool = False,
        prefetch_count: Optional[int] = None
    ) -> None:
        """
        큐로부터 메시지 소비를 시작합니다.
        
        Args:
            queue_name: 소비할 큐 이름
            callback: 메시지를 처리할 비동기 콜백 함수
                     (message: aio_pika.IncomingMessage)를 인자로 받아야 함
            auto_ack: 메시지 자동 확인
            prefetch_count: 미리 가져올 메시지 수
        """
        if not self.channel:
            raise RuntimeError("채널이 초기화되지 않았습니다. 먼저 connect()를 호출하세요.")

        if prefetch_count:
            await self.channel.set_qos(prefetch_count=prefetch_count)

        queue = await self.declare_queue(queue_name)
        
        async def process_message(message: aio_pika.IncomingMessage) -> None:
            async with message.process(ignore_processed=auto_ack):
                try:
                    body = json.loads(message.body.decode())
                    await callback(body, message)
                except json.JSONDecodeError:
                    # JSON이 아닌 경우, 원본 바디를 전달
                    await callback(message.body.decode(), message)

        await queue.consume(process_message, no_ack=auto_ack)

    async def bind_queue(
        self,
        queue_name: str,
        exchange_name: str,
        routing_key: str = ""
    ) -> None:
        """
        큐를 익스체인지에 라우팅 키로 바인딩합니다.
        
        Args:
            queue_name: 큐 이름
            exchange_name: 익스체인지 이름
            routing_key: 바인딩을 위한 라우팅 키
        """
        if not self.channel:
            raise RuntimeError("채널이 초기화되지 않았습니다. 먼저 connect()를 호출하세요.")

        queue = await self.declare_queue(queue_name)
        exchange = await self.channel.get_exchange(exchange_name)
        await queue.bind(exchange, routing_key=routing_key)

    @asynccontextmanager
    async def get_channel(self):
        """
        작업을 위한 채널을 가져오는 컨텍스트 매니저.
        채널 생명주기를 자동으로 관리합니다.
        """
        if not self.connection:
            await self.connect()
        
        channel = await self.connection.channel()
        try:
            yield channel
        finally:
            await channel.close()

    @property
    def is_connected(self) -> bool:
        """클라이언트가 RabbitMQ에 연결되어 있는지 확인합니다."""
        return self._is_connected and self.connection and not self.connection.is_closed


# 애플리케이션 전역에서 사용할 싱글톤 인스턴스
rabbitmq_client: Optional[RabbitMQClient] = None


def get_rabbitmq() -> RabbitMQClient:
    """
    RabbitMQ 클라이언트 인스턴스를 가져옵니다.
    
    Returns:
        RabbitMQClient 인스턴스
        
    Raises:
        RuntimeError: 클라이언트가 초기화되지 않은 경우
    """
    if rabbitmq_client is None:
        raise RuntimeError(
            "RabbitMQ 클라이언트가 초기화되지 않았습니다. "
            "애플리케이션 시작 시 init_rabbitmq()를 호출하세요."
        )
    return rabbitmq_client


async def init_rabbitmq(url: str, connection_name: str = "fastapi-service") -> RabbitMQClient:
    """
    애플리케이션의 RabbitMQ 클라이언트를 초기화합니다.
    
    Args:
        url: RabbitMQ 연결 URL
        connection_name: 연결 이름
        
    Returns:
        초기화된 RabbitMQClient 인스턴스
    """
    global rabbitmq_client
    rabbitmq_client = RabbitMQClient(url, connection_name)
    await rabbitmq_client.connect()
    return rabbitmq_client


async def close_rabbitmq() -> None:
    """RabbitMQ 연결을 종료합니다."""
    global rabbitmq_client
    if rabbitmq_client:
        await rabbitmq_client.disconnect()
        rabbitmq_client = None
