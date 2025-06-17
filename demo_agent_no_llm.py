# This file demonstrates a basic team of agents using Autogen.
# It showcases a TaskIssuer agent that generates tasks and an Executor agent that (implicitly) handles them.
# The agents communicate via messages within a single-threaded runtime environment.
#
# This is a minimal example using the AutoGen Core API to spin up three agents—TaskIssuer,
# Executor, and Terminator—that count from 1 to 100. The TaskIssuer issues the next
# number, the Executor “runs” it (prints it), and the Terminator watches for 100 and
# then signals completion. We leverage the SingleThreadedAgentRuntime, RoutedAgent,
# and the @default_subscription/@message_handler decorators from the Core API to wire
# everything together.




import asyncio
from dataclasses import dataclass

from autogen_core import (
    DefaultTopicId,
    MessageContext,
    RoutedAgent,
    default_subscription,
    message_handler,
    SingleThreadedAgentRuntime,
)

@dataclass
class Message:
    content: str

@default_subscription
class TaskIssuer(RoutedAgent):
    def __init__(self) -> None:
        super().__init__("TaskIssuer")
        self.counter = 0

    @message_handler
    async def handle_message(self, message: Message, ctx: MessageContext) -> None:
        # Issue the next task until we hit 100
        if self.counter < 100:
            self.counter += 1
            task = str(self.counter)
            print(f"TaskIssuer: Issuing task {task}")
            await self.publish_message(Message(content=task), DefaultTopicId())

@default_subscription
class Executor(RoutedAgent):
    def __init__(self) -> None:
        super().__init__("Executor")

    @message_handler
    async def handle_message(self, message: Message, ctx: MessageContext) -> None:
        # “Execute” the task by printing it, then republish so Terminator sees it
        print(f"Executor: Executing task {message.content}")
        await self.publish_message(message, DefaultTopicId())

@default_subscription
class Terminator(RoutedAgent):
    def __init__(self) -> None:
        super().__init__("Terminator")

    @message_handler
    async def handle_message(self, message: Message, ctx: MessageContext) -> None:
        # When 100 arrives, announce completion
        if message.content == "100":
            print("Terminator: All tasks completed. Goodbye!")

async def main() -> None:
    # 1) Create a local runtime
    runtime = SingleThreadedAgentRuntime()
    # 2) Register each agent type
    await TaskIssuer.register(runtime, "task_issuer", lambda: TaskIssuer())
    await Executor.register(runtime, "executor", lambda: Executor())
    await Terminator.register(runtime, "terminator", lambda: Terminator())
    # 3) Start the runtime and fire off an initial “kick-off” message
    runtime.start()
    await runtime.publish_message(Message(content="start"), DefaultTopicId())
    # 4) Wait until all agents are idle (i.e. no more messages in flight)
    await runtime.stop_when_idle()

if __name__ == "__main__":
    asyncio.run(main())
