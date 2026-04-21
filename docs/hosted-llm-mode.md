# Hosted LLM Mode

## Goal
Keep the game server light by moving model inference out of the game host.

## AIA behavior
- rule engine stays in AIA
- agent graph stays in AIA
- model inference is delegated to an external hosted API
- returned JSON action is parsed and validated before use

## Recommended mode
- `LLM_BACKEND=hosted`
- `LLM_PROVIDER=openai_compatible`
- `LLM_BASE_URL=<hosted-api-base-url>`
- `LLM_MODEL=<remote-model-name>`
- `LLM_API_KEY=<secret>`

## Why this is lighter
- no local model weights on the game host
- less RAM pressure on the game server machine
- simpler deployment for multiple worlds

## Safety rule
Even in hosted mode, AIA only returns one allowed action and the game server remains the final executor.
