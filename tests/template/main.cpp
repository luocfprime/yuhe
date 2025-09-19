#include <iostream>
#include <cstdlib>

// === AUTO-GENERATED FUNCTION WILL BE INSERTED HERE ===
// {{IS_POINT_IN_BOX_FUNCTION}}

int main(int argc, char** argv) {
    if(argc < 4) {
        std::cerr << "Usage: " << argv[0] << " x y z\n";
        return 1;
    }
    double x = std::atof(argv[1]);
    double y = std::atof(argv[2]);
    double z = std::atof(argv[3]);
    bool inside = is_point_in_box(x,y,z);
    std::cout << (inside ? 1 : 0) << std::endl;
    return 0;
}
