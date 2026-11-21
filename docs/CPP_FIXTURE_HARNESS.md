# C++ fixture verification

This milestone adds independently authored, manifest-bound C++ fixtures and an
explicit compile/link/sanitizer runner. It does not change the static-only
contract of `debug-cpp`.

## Fixture inventory

| Fixture ID | Expected result | Intended failure |
|---|---|---|
| `cpp.compile.unique-ptr-copy.v1` | `COMPILE_FAIL` | Copying a `std::unique_ptr`; compiler must diagnose the deleted copy constructor |
| `cpp.link.pure-virtual-dtor.v1` | `LINK_FAIL` | C++98 pure virtual destructor declared but not defined; compiler succeeds, linker cannot resolve the destructor |
| `cpp.asan.heap-use-after-free.v1` | `ASAN_FINDING` | Read through a stale pointer after deleting its allocation |
| `cpp.ubsan.signed-overflow.v1` | `UBSAN_FINDING` | Signed integer overflow |
| `cpp.clean.unique-ptr-transfer.v1` | `CLEAN` | Valid move-based transfer of exclusive ownership; run separately under ASan and UBSan |
| `cpp.forwarding.lvalue-rvalue.v1` | `CLEAN` | Correct forwarding-reference template preserves lvalue and rvalue overload selection |
| `cpp.forwarding.incorrect-move.v1` | `BEHAVIOR_REPRODUCED` | Negative control deliberately uses `std::move` and misroutes an lvalue to the rvalue overload |
| `cpp.forwarding.value-category-cxx17.v1` | `CLEAN` | C++17 `static_assert` probes verify lvalue, rvalue, const-lvalue, and const-rvalue reference types |
| `cpp.thread.data-race.v1` | `TSAN_FINDING` | Two threads perform unsynchronized writes to one shared counter |
| `cpp.thread.mutex-control.v1` | `CLEAN` | The same counter workload is protected by a mutex and should be clean under TSan |

The fixtures carry an MIT SPDX tag, an independent-origin marker, and a
manifest-pinned SHA-256. The harness refuses to execute a fixture if its bytes
do not match that pin. No source from the external BartVandewoestyne
repositories is included. Their existing metadata-only records remain on
`UNVERIFIED_HOLD`.

## Run one fixture

The global `--db` option appears before the subcommand:

```sh
body-of-secrets --db data/archive.db verify-cpp \
  --fixture cpp.asan.heap-use-after-free.v1 \
  --compiler g++ --json
```

Supported compiler names are `g++` and `clang++`. Only fixture IDs from the
checked-in manifest are accepted; arbitrary source paths and caller-supplied
compiler flags are not accepted.

## Evidence and result states

The harness compiles to an object first, then links separately, so a compile
failure cannot be mistaken for the intended link failure. Expected compiler and
linker failures also require diagnostic signatures associated with the target
failure (deleted copy constructor; unresolved `Interface::~Interface()`).

Sanitizers are probed before the fixture is run. A missing or unusable sanitizer
runtime is recorded as `SANITIZER_UNAVAILABLE`, never as `CLEAN`. In particular,
ThreadSanitizer may be unavailable for a given compiler/runtime image; in that case
the TSan fixture is explicitly inconclusive and its `passed` field remains false.
The test suite accepts that availability state without treating it as a clean run.
Timeouts, unexpected compile/link failures, execution failures, expected sanitizer
findings, and deliberately reproduced negative-control behavior remain distinct
outcomes.

Each verification is archived as a separate record. The static report from
`debug-cpp` is not overwritten, and a sanitizer finding does not automatically
promote every related Expert hypothesis to a verified root cause.

## Boundaries

- No shell invocation; subprocesses receive argument arrays with `shell=False`.
- No network or dependency-fetch step is performed by the harness.
- Compiler and executable timeouts are bounded by the fixture manifest.
- Output is bounded before it is archived.
- Temporary build products are removed after each fixture run.
- ASan, UBSan, and TSan are run separately. TSan race and mutex-control fixtures are paired.
- Forwarding tests include a correct lvalue/rvalue control, an intentionally incorrect `std::move` negative control, and C++17 compile-time value-category assertions.
- Expert rules consume fixture identifiers and observed outcomes as supporting evidence only; results remain `[PLAUSIBLE]` / `[NOT_VERIFIED]` and never auto-verify a root cause.
- This is a controlled fixture harness, not yet a general-purpose sandbox for
  untrusted user projects. Do not pass arbitrary third-party source to it.

## CI

`.github/workflows/cpp-fixture-verification.yml` runs the fixture tests under
GCC and Clang on Ubuntu. The harness probes each sanitizer runtime independently;
CI records unavailable TSan runtimes as inconclusive rather than converting them
to clean results. OS-level resource-limit enforcement and a broader isolated
sandbox remain future work.
