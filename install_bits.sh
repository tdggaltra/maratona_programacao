#!/bin/bash
# Script para criar o header bits/stdc++.h no macOS

# Encontra o diretório de includes do g++
INCLUDE_DIR=$(g++ -v 2>&1 | grep "End of search list" -B20 | grep "^ " | tail -1 | sed 's/^ *//')

if [ -z "$INCLUDE_DIR" ]; then
    echo "Não foi possível encontrar o diretório de includes do g++"
    echo "Tente usar: /usr/local/include"
    INCLUDE_DIR="/usr/local/include"
fi

echo "Usando diretório: $INCLUDE_DIR"

# Cria o diretório bits se não existir
sudo mkdir -p "$INCLUDE_DIR/bits"

# Cria o arquivo stdc++.h
sudo tee "$INCLUDE_DIR/bits/stdc++.h" > /dev/null << 'EOF'
// C++ includes used for competitive programming
#include <iostream>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <string>
#include <vector>
#include <list>
#include <set>
#include <map>
#include <queue>
#include <stack>
#include <algorithm>
#include <numeric>
#include <utility>
#include <sstream>
#include <iomanip>
#include <climits>
#include <cfloat>
#include <cassert>
#include <fstream>
#include <functional>
#include <iterator>
#include <deque>
#include <bitset>
#include <unordered_map>
#include <unordered_set>
#include <array>
#include <tuple>
#include <regex>
#include <random>
#include <chrono>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <future>
#include <atomic>
#include <memory>
#include <exception>
#include <stdexcept>
#include <new>
#include <typeinfo>
#include <complex>
#include <valarray>
#include <cctype>
#include <cwctype>
#include <ctime>
#include <locale>
#include <codecvt>

using namespace std;
EOF

echo "Arquivo bits/stdc++.h criado com sucesso em: $INCLUDE_DIR/bits/stdc++.h"