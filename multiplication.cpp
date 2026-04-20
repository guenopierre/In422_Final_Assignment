#include <iostream>
#include <cstdlib>
#include <ctime>

int main(){
    srand((unsigned)time(NULL));
    int a = 1000 + rand() % 901;
    int b = 1500 + rand() % 901;
    int c = 1000 + rand() % 901;
    int d = 1500 + rand() % 901;
    int e = 2000 + rand() % 901;
    std::cout << a*b*c*d*e << std::endl;
    return 0;
}