// SPDX-License-Identifier: MIT
// Origin: independently authored BODY OF SECRETS ThreadSanitizer fixture.
#include <thread>

int shared_counter = 0;

void increment() {
    for (int index = 0; index < 10000; ++index) {
        ++shared_counter; // Deliberate unsynchronized conflicting write.
    }
}

int main() {
    std::thread first(increment);
    std::thread second(increment);
    first.join();
    second.join();
    return 0;
}
