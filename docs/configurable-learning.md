# Progress and assessment configuration

The gameplay rail and save-slot menu share the same stage progress rules.
Progress and Topic Guidance are available by default for any stage whose
`manual.topics` contains lessons. A stage can explicitly set
`progress.enabled` to `False` to hide those two buttons. This never changes
its gate requirements or campaign rewards.

A stage may supply `progress.unfinished_content_message` for the state where
all available lessons are passed but `completion.content_ready` is false.
Omitting the message uses a generic fallback rather than naming another stage.
Boss progress includes victories in other room checkpoints. The active room's
live state supersedes its older checkpoint, as it does for stage gates.
Save-slot percentages now include the configured final assessment for every
stage; completing lessons and the boss alone cannot report full completion.

## Assessment structure

The existing `stage1_final` and `stage1_integrated` validator names remain
supported. Their classes delegate to `StructureValidator`; each challenge
supplies an ordered, non-empty `structure_requirements` list. Existing runtime
value checks, hidden test cases, output checks, timers, and rotations still run.
A missing or invalid structure contract fails validation rather than granting
completion.

Each rule has a `kind` and optional learner-facing `feedback`:

| Kind | Configuration |
| --- | --- |
| `variables` | `names`; optional `include_all_stores` |
| `input` | `target`; optional `single_target` |
| `cast` | `function`, `source`; optional assignment `target`, `exactly_one_arg` |
| `aug_assign` | `target`, AST `operator` name such as `Add`, literal `value` |
| `arithmetic` | Any binary operation or augmented assignment |
| `if_elif_else` | Optional `first_top_level` to constrain the first top-level decision |
| `f_string` | Optional assignment `target` |
| `method` | `method`; optional receiver `source`, assignment `target` |
| `print` | Optional sole argument `source` |

`structure_success` optionally supplies the success message. Structure checks
establish required syntax, not correctness; the sandbox and behavioral test
cases establish the result. The original Island assessment retains its
assignment-specific checks; the three retakes retain their existing concept
checks. No assessment was made easier by this refactor.

## Function exercises

Function challenges may provide `required_constructs`, using any of `for`,
`while`, `break`, `continue`, and `try`. Requirements apply regardless of the
function's name. For example, the skip-invalid-readings exercise authors
`('break', 'continue')` in its challenge data. Its existing `learning_construct`,
helper-function checks, argument-preservation checks, and runtime cases remain
in force. Unknown required constructs fail validation.
