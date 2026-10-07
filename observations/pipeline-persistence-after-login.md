# Pipeline Persistence After Reauthentication

## Observation

After logging out of Rhombus and signing back in, the project and AI Builder
conversation history remained available, but the pipeline canvas appeared empty.

AI Builder nevertheless reported that the pipeline was already in the correct
baseline configuration and that the transformation nodes were intact.

## Expected

The pipeline canvas should restore the saved project state consistently after
reauthentication.

## Actual

The persisted AI Builder history described a complete pipeline while the canvas
contained no visible pipeline nodes.

The baseline pipeline had to be rebuilt through AI Builder before continuing
testing.

## Impact

This creates ambiguity over whether project state, conversational state, and
executable pipeline state are persisted together. It also makes it difficult for
a user to know whether a pipeline has genuinely been lost or is simply not being
rendered.

## Evidence

See
[`evidence/pipeline-persistence-after-login.png`](evidence/pipeline-persistence-after-login.png).