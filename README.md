# CASTEP Linter

This is a code linter for the [CASTEP](http://www.castep.org) project to enforce certain style features.

## Docker

Each release is also published as a Docker image. To lint files in the current directory:

```sh
docker run --rm -v "$PWD:/src" ghcr.io/byornski/castep-linter file.f90
```

Add `--user "$(id -u):$(id -g)"` so that any reports written with `-x`, `-j` or `-c` are owned by you rather than root. To build the image from this repository instead, run `docker build -t castep-linter .`.

Images up to version 0.8.0 were published on Docker Hub as `byornski/castep-linter`; later versions are only on the GitHub Container Registry.

## Checks

Each problem found is an error, a warning or info. `castep-lint` exits with a failure if it finds a problem at or above the level given with `-l`, which is `Info` by default. Each check has a name, used to disable it and in the reports.

### `TRACE`: routines are traced

Every subroutine and function calls `trace_entry` and `trace_exit`, passing its own name, either as a string or as a `character` parameter. The name `castep` is also accepted. `trace_exit` must be the statement immediately before every `return` after `trace_entry`, and the last statement of the routine. It is not needed after `io_abort`, `io_allocate_abort`, `err_abort`, `stop` or `go to`, and at the end of the routine an `if` block with an `else` is accepted if each branch ends this way. Routines declared in an `interface` block are not checked.

```fortran
subroutine x()
  call trace_entry('x', status)
  if (failed) then
    call trace_exit('x', status)
    return
  end if
  call trace_exit('x', status)
end subroutine x
```

| Problem | Level |
|---|---|
| Missing trace_entry in x | Info |
| Missing trace_exit in x, for a routine which does not call `trace_entry` | Info |
| Missing trace_exit before return in x, including `if (...) return` | Error |
| trace_exit is not immediately before return in x | Error |
| Missing trace_exit at end of x | Error |
| trace_exit is not at the end of x | Error |
| Incorrect name passed to trace in x | Error |
| No name passed to trace in x | Error |
| Unidentified variable v passed to trace in x, for a name in a variable which is not a `character` parameter | Error |
| Unrecognised name passed to trace in x, eg `names(1)` | Error |

Trace calls inside an `if`, loop or `#ifdef` which name a different routine are taken to time a section of the routine, so are not checked.

### `ALLOC`: allocate status is checked

Every `allocate` has a `stat=` variable, and the next statement is an `if` which compares it, eg `if (ierr /= 0)`. A compound condition, such as `if (ierr /= 0 .and. on_root)`, does not count.

| Problem | Level |
|---|---|
| No stat on allocate statement | Warning |
| Allocate status not checked | Error |

### `ALLOC_ABORT`: allocate failures are reported

When an `allocate`'s status is checked, the `if` reports the failure with one of the error routines: `io_allocate_abort`, `io_abort`, `err_abort` or `err_assert`. Other routines, including `comms_abort`, and `stop` are reported. `io_allocate_abort` is given exactly the name of the array allocated, eg `'obj%arr'`, and of the routine or program it is in. The names may also be given in `character` variables declared with a value in the routine, eg `character(len=*), parameter :: subroutine_name = 'x'`. Names in other variables, such as arguments, are not checked.

```fortran
allocate(obj%arr(n), stat=ierr)
if (ierr /= 0) call io_allocate_abort('obj%arr', 'x')
```

| Problem | Level |
|---|---|
| Allocation failure does not raise an error | Error |
| Wrong array name used in io_allocate_abort. Expected: … | Error |
| Wrong subroutine name used in io_allocate_abort. Expected: … | Error |
| Wrong array name used in io_allocate_abort by variable v="…". Expected: … | Error |
| Wrong subroutine name used in io_allocate_abort by variable v="…". Expected: … | Error |

### `KIND`: reals and complexes are double precision

`real` and `complex` declarations give their kind as `kind=dp`. `dprec`, `di_dp` and `version_kind` are also accepted.

| Example | Problem | Level |
|---|---|---|
| `real :: a` | No kind specifier | Error |
| `real(8) :: a`, `real*8 :: a` | Numeric kind specifier | Error |
| `real(kind=sp) :: a` | Invalid kind specifier | Warning |
| `real(dp) :: a` | Kind specified without keyword | Info |
| `double precision :: a` | double precision used instead of real(kind=dp) | Warning |
| `double complex :: z` | double complex used instead of complex(kind=dp) | Warning |

### `LITERAL_KIND`: number literals have a kind

Real literals have a double precision kind, eg `1.0_dp`, or a `d` exponent, eg `1.0d0`. Integer literals need no kind, but any kind given is `int32` or `int64`.

| Example | Problem | Level |
|---|---|---|
| `1.0` | Float literal without kind | Error |
| `1.0_sp` | Float literal with kind='sp' | Error |
| `3_8` | Integer literal with kind='8' | Error |

### `CMPLX_KIND`: complex numbers are double precision

`cmplx` is given a double precision kind, eg `cmplx(a, b, kind=dp)` or `cmplx(a, b, dp)`.

| Example | Problem | Level |
|---|---|---|
| `cmplx(a, b)` | No kind specifier in complex intrinsic | Error |
| `cmplx(a, b, sp)` | Invalid kind specifier in complex intrinsic | Error |

## Disabling checks

Checks can be switched off with a `castep-lint: disable=` comment, giving the names of one or more of the checks above, separated by commas (case does not matter).

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

An unknown name, a comment which names no checks or does not apply to anything, and a malformed comment are reported as warnings named `DIRECTIVE`, which cannot be disabled.
