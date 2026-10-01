/* SPDX-License-Identifier: Apache-2.0 */
#pragma once

// Affected: ESP-IDF 6.0.1 + its GCC 15.2 Picolibc toolchain, C++23.
// Upstream issue: hal/assert.h leaves __noreturn as [[noreturn]], which is
// invalid at Picolibc's suffix attribute sites when board headers precede libc.
// No upstream issue number has been assigned in this repository.
// Remove when the locked IDF/toolchain compiles the affected display TU with
// -Werror=attributes and no forced include. Preserve the noreturn semantics.
#include "hal/assert.h"

#if CONFIG_LIBC_PICOLIBC && defined(__cplusplus)
#undef __noreturn
#define __noreturn __attribute__((__noreturn__))
#endif
