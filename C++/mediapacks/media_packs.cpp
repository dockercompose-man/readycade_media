#include <QApplication>
#include <QWidget>
#include <QVBoxLayout>
#include <QComboBox>
#include <QPushButton>
#include <QLabel>

class MediaPackSelector : public QWidget {
    Q_OBJECT

public:
    MediaPackSelector(QWidget *parent = nullptr) : QWidget(parent) {
        // Set up layout
        QVBoxLayout *layout = new QVBoxLayout(this);

        // Create a label
        QLabel *label = new QLabel("Select Media Pack:", this);
        layout->addWidget(label);

        // Create a combo box for media pack selection
        mediaPackComboBox = new QComboBox(this);
        mediaPackComboBox->addItem("Media Pack 1");
        mediaPackComboBox->addItem("Media Pack 2");
        mediaPackComboBox->addItem("Media Pack 3");
        layout->addWidget(mediaPackComboBox);

        // Create a button to perform an action (e.g., open media pack)
        QPushButton *openButton = new QPushButton("Open Media Pack", this);
        connect(openButton, &QPushButton::clicked, this, &MediaPackSelector::openMediaPack);
        layout->addWidget(openButton);

        // Set up the main window
        setLayout(layout);
        setWindowTitle("Media Pack Selector");
        setFixedSize(300, 150);
    }

private slots:
    void openMediaPack() {
        // Get the selected media pack from the combo box
        QString selectedMediaPack = mediaPackComboBox->currentText();

        // Perform an action, e.g., open the selected media pack
        // You can replace this with your specific functionality
        // For simplicity, we just print the selected media pack
        qDebug() << "Opening Media Pack: " << selectedMediaPack;
    }

private:
    QComboBox *mediaPackComboBox;
};

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);

    // Create and show the media pack selector window
    MediaPackSelector mediaPackSelector;
    mediaPackSelector.show();

    // Run the application
    return app.exec();
}
