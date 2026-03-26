#!/bin/bash
set -e

echo "Starting GROBID installation..."
PROJECT_ROOT="/home/naturalis/programs/hyperbolic_KG"
cd "$PROJECT_ROOT"

# Step 1: Clone only if directory does not exist
if [ ! -d "grobid" ]; then
    echo "Cloning GROBID repository..."
    git clone https://github.com/kermitt2/grobid.git
fi

cd grobid

# Step 2: Build only if the service JAR does not exist yet
# The JAR is produced at grobid-service/build/libs/ after a successful build
GROBID_JAR=$(find . -path "*/grobid-service/build/libs/grobid-service-*.jar" \
    -not -name "*sources*" \
    -not -name "*javadoc*" 2>/dev/null | head -1)

if [ -z "$GROBID_JAR" ]; then
    echo "Building GROBID (this uses cached Gradle dependencies, ~5-10 min)..."
    # -x flags skip Maven publication tasks that are incompatible with Gradle 9
    # due to removed getDependencyProject() API. These tasks produce no runtime artifact.
    ./gradlew clean install --no-daemon \
        -x :grobid-trainer:generatePomFileForMavenJavaPublication \
        -x :grobid-trainer:publishMavenJavaPublicationToMavenLocal
    echo "GROBID built successfully."
else
    echo "GROBID JAR already built: $GROBID_JAR"
fi

cd "$PROJECT_ROOT"
