import asyncio
import pytest
from app.events import event_bus, NoteCreatedEvent


class TestEventBus:
    def setup_method(self):
        event_bus._subscribers.clear()

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self):
        results = []

        async def handler(event):
            results.append(event.ts_code)

        event_bus.subscribe("note_created", handler)
        await event_bus.publish(
            "note_created", NoteCreatedEvent(ts_code="000001.SZ", note_content="test")
        )

        assert results == ["000001.SZ"]

    @pytest.mark.asyncio
    async def test_multiple_subscribers_receive_event(self):
        results = []

        async def handler1(event):
            results.append(f"h1:{event.ts_code}")

        async def handler2(event):
            results.append(f"h2:{event.ts_code}")

        event_bus.subscribe("note_created", handler1)
        event_bus.subscribe("note_created", handler2)
        await event_bus.publish(
            "note_created", NoteCreatedEvent(ts_code="000001.SZ", note_content="test")
        )

        assert "h1:000001.SZ" in results
        assert "h2:000001.SZ" in results

    @pytest.mark.asyncio
    async def test_publish_with_no_subscribers(self):
        await event_bus.publish(
            "note_created", NoteCreatedEvent(ts_code="000001.SZ", note_content="test")
        )

    @pytest.mark.asyncio
    async def test_async_handler(self):
        results = []

        async def async_handler(event):
            await asyncio.sleep(0.001)
            results.append(event.ts_code)

        event_bus.subscribe("note_created", async_handler)
        await event_bus.publish(
            "note_created", NoteCreatedEvent(ts_code="000001.SZ", note_content="test")
        )

        assert results == ["000001.SZ"]

    @pytest.mark.asyncio
    async def test_event_type_isolation(self):
        results = []

        async def handler(event):
            results.append(event.ts_code)

        event_bus.subscribe("note_created", handler)
        await event_bus.publish(
            "other_event", NoteCreatedEvent(ts_code="000001.SZ", note_content="test")
        )

        assert results == []
