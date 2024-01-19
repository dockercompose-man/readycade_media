#include <iostream>
#include <vector>
#include <string>

int main() {
    // Define media packs
    std::vector<std::string> mediaPacks = {
        "64dd-media.7z",
        "amiga600-media.7z",
        "amiga1200-media.7z",
        // ... add more media packs as needed
    };

    // Display media packs to the user
    std::cout << "Choose a media pack to download:" << std::endl;
    for (int i = 0; i < mediaPacks.size(); ++i) {
        std::cout << i + 1 << ". " << mediaPacks[i] << std::endl;
    }

    // Prompt user for selection
    std::cout << "Enter the number of the media pack you want to download: ";
    int choice;
    std::cin >> choice;

    // Validate user's choice
    if (choice < 1 || choice > mediaPacks.size()) {
        std::cout << "Invalid choice. Please enter a valid number." << std::endl;
        return 1;
    }

    // Get selected media pack name
    std::string selectedMediaPack = mediaPacks[choice - 1];

    // Display download message
    std::cout << "Downloading " << selectedMediaPack << "..." << std::endl;

    // TODO: Implement the download logic here

    // Display download completion message
    std::cout << "Download completed." << std::endl;

    // TODO: Implement additional logic for checksum verification, extraction, and copying to the network share

    // Display final message
    std::cout << "Enjoy your Readycade!" << std::endl;
    std::cout << "Press any key to exit." << std::endl;

    // Wait for user input before exiting
    std::cin.ignore();
    std::cin.get();

    return 0;
}
