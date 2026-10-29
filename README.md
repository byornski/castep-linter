# CASTEP Linter

This is a code linter for the [CASTEP](http://www.castep.org) project to enforce certain style features.

## Disabling checks

Checks can be switched off with a `castep-lint: disable=` comment, giving one or more check names separated by commas (case does not matter).

```fortran
subroutine comms_abort()
  ! castep-lint: disable=trace
  ...
  x = 1.0  ! castep-lint: disable=literal_kind
  allocate(a(n), &
           b(n))  ! castep-lint: disable=alloc
end subroutine comms_abort
```

- **A whole subroutine or function:** put the comment on its own line directly in the body of the routine, or after the `subroutine`/`function` line. Routines contained within it are not affected.
- **A single statement:** put the comment after the code. It covers every line of a statement continued with `&`, so it can go on any of those lines.

| Name | Check |
|---|---|
| `TRACE` | Subroutines and functions call `trace_entry` and `trace_exit` with their own name |
| `ALLOC` | `allocate` statements have a `stat` which is checked straight afterwards |
| `KIND` | `real` and `complex` declarations have a `kind=dp` |
| `LITERAL_KIND` | Real literals have a `_dp` kind and integer literals a valid kind |
| `CMPLX_KIND` | `cmplx(...)` is given a `kind=dp` |

These are also the `check_name`s in the CodeClimate report. An unknown name, or a comment which does not apply to anything, is reported as a warning.
