// SPDX-License-Identifier: MIT
// Origin: independently authored BODY OF SECRETS ThreadSanitizer control fixture.
#include <mutex>
#include <thread>

int shared_counter = 0;
std::mutex counter_mutex;

void increment() {
    for (int index = 0; index < 10000; ++index) {
        std::lock_guard<std::mutex> lock(counter_mutex);
        ++shared_counter;
    }
}

int main() {
    std::thread first(increment);
    std::thread second(increment);
    first.join();
    second.join();
    return shared_counter == 20000 ? 0 : 1;
}
