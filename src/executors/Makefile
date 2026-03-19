
# Compiler
CXX = g++

# Base flags
CXXFLAGS_BASE = -std=c++17 -I./ -Wall -I/usr/local/include

# Base libs
LDFLAGS = -L/usr/local/lib
LIBS_BASE = -lpthread -lyaml-cpp

# Target executable name
TARGET = executor

# Base files
STATIC_SOURCES = main.cpp factory.cpp

OBJECTS = $(SOURCES:.cpp=.o)

$(TARGET): $(OBJECTS)
	@echo "--- Linkando o executável '$(TARGET)' ---"
	$(CXX) -o $@ $^ $(LDFLAGS) $(LIBS)
	@echo "--- Executável '$(TARGET)' criado com sucesso! ---"

$(OBJECTS): %.o: %.cpp
	@mkdir -p $(dir $@)
	@echo "Compilando $< ..."
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	@echo "--- Limpando arquivos de build ---"
	find . -type f -name "*.o" -delete
	rm -f $(TARGET)
	@echo "--- Limpeza concluída ---"


# -- ADD NEW STRATEGIES BELOW THIS LINE --

# Don't forget to add new strategie alias to the .PHONY list below
.PHONY: all redis http clean

all: redis

# TEMPLATE FOR NEW STRATEGIES
# strategy_name:
#	$(MAKE) $(TARGET) \
#		SOURCES="$(STATIC_SOURCES) path/to/strategy.cpp" \
#		CXXFLAGS="$(CXXFLAGS_BASE) -DBUILD_STRATEGY_NAME" \
#		LIBS="additional_libs $(LIBS_BASE)"

redis:
	$(MAKE) $(TARGET) \
		SOURCES="$(STATIC_SOURCES) redis/redis.cpp" \
		CXXFLAGS="$(CXXFLAGS_BASE) -DBUILD_REDIS_STRATEGY" \
		LIBS="-lredis++ -lhiredis $(LIBS_BASE)"

http:
	$(MAKE) $(TARGET) \
		SOURCES="$(STATIC_SOURCES) http/http.cpp" \
		CXXFLAGS="$(CXXFLAGS_BASE) -DBUILD_HTTP_STRATEGY" \
		LIBS="-lcurl $(LIBS_BASE)"