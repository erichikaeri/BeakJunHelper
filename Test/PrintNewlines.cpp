#include <iostream>

int main()
{
    int input;
    std::cin >> input;

    for (int i = 0 ; i < input; i++)
    {
        printf("%d\n", i + 1);
    }
}