#pragma once

#include <algorithm>
#include <cstddef>

namespace espocket {

struct LauncherPage {
    size_t index;
    size_t count;
    size_t begin;
    size_t end;
};

inline LauncherPage launcher_page(size_t dynamic_count, size_t requested)
{
    const auto rows = dynamic_count + 4;
    const auto pages = (rows + 3) / 4;
    const auto index = std::min(requested, pages - 1);
    return {index, pages, index * 4, std::min(rows, (index + 1) * 4)};
}

}
