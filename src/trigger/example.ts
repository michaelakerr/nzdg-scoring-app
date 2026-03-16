import { logger, task, wait } from "@trigger.dev/sdk/v3";
import {python} from "@trigger.dev/python";

export const helloWorldTask = task({
  id: "hello-world",
  // Set an optional maxDuration to prevent tasks from running indefinitely
  maxDuration: 300, // Stop executing after 300 secs (5 mins) of compute
  run: async (payload: any, { ctx }) => {
    logger.log("Hello, world!", { payload, ctx });

    await wait.for({ seconds: 5 });

    return {
      message: "Hello, world!",
    }
  },
});

export const triggerPlayerUpdatesPython = task({
  id: "trigger_tournament_added",
  run: async (payload: any, { ctx }) => {
    console.log("Triggering tournament added Python script", { payload, ctx });
    const result = await python.runScript("./trigger_tournament_added.py", [payload.event_id]);
    return result.stdout;
  },
});
