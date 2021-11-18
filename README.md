# USSR
Ultimate Score Server for RealistikOsu (well not just us but it makes the acronym work.)
*Also I wonder how long this name will last*.

![Speed FLex](https://i.imgur.com/31fYbHP.png)


## What is this?

The primary objective of the USSR is to serve as an almost drag and drop replacement for Ripple's [LETS](https://github.com/osuripple/lets) as a score server. This means for existing server owners:
- Usage of the usual Ripple database schema.
- Full usage of the Ripple Redis API (pubsubs, keys etc).
- Full support of the Ripple JSON API.

All of this while also MASSIVELY improving upon LETS in the following areas:
- Massive performance gains
- Significantly more efficient with the database and other resources
- Modern asynchronous Python architecture
- Maintainable, modifiable codebase

## Extras
Alongside the main score server portion, USSR features multiple tools available within the CLI to assist you with your server!

### PP System Estimation Tool
![Result Example](https://i.imgur.com/nkd09L5.png)
This tool aims to help you experiment with new PP system changes, displaying the effects it would have on a user's scores.
