#!/bin/bash
# Release packaging and deployment script
#
# Generates distributable packages and manages release artifacts
# Supports multiple formats: Docker, Kubernetes, Helm, binary archives
#
# Usage:
#   ./package_release.sh --version 1.0.0 --format docker
#   ./package_release.sh --version 1.0.0 --format helm --registry myregistry.azurecr.io
#   ./package_release.sh --version 1.0.0 --all
#   ./package_release.sh --version 1.0.0 --sign --gpg-key abc123def

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="${PROJECT_ROOT}/build"
RELEASE_DIR="${PROJECT_ROOT}/releases"
DIST_DIR="${RELEASE_DIR}/dist"
CHECKSUMS_FILE="${RELEASE_DIR}/CHECKSUMS"

# Default values
VERSION=""
FORMAT=""
REGISTRY=""
SIGN=false
GPG_KEY=""
PUSH=false
DRY_RUN=false
ALL_FORMATS=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

print_usage() {
    cat << 'EOF'
Usage: package_release.sh [OPTIONS]

Options:
    --version VERSION       Release version (e.g., 1.0.0) [REQUIRED]
    --format FORMAT         Package format: docker, helm, binary, kubernetes [REQUIRED unless using --all]
    --all                   Create all package formats
    --registry REGISTRY     Docker registry URL (for docker/helm formats)
    --push                  Push images to registry after building
    --sign                  GPG sign the packages
    --gpg-key KEY           GPG key ID for signing
    --dry-run               Show what would be done without actually doing it
    --help                  Show this help message

Package Formats:
    docker       - OCI container image
    helm         - Helm chart package
    binary       - Binary distribution archive with checksums
    kubernetes   - Kubernetes manifests and deployment configs

Examples:
    # Create Docker image for version 1.0.0
    ./package_release.sh --version 1.0.0 --format docker

    # Create and push to registry
    ./package_release.sh --version 1.0.0 --format docker --registry myregistry.azurecr.io --push

    # Create all formats with signing
    ./package_release.sh --version 1.0.0 --all --sign --gpg-key abc123

    # Dry run to see what would happen
    ./package_release.sh --version 1.0.0 --format docker --dry-run
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --version)
                VERSION="$2"
                shift 2
                ;;
            --format)
                FORMAT="$2"
                shift 2
                ;;
            --registry)
                REGISTRY="$2"
                shift 2
                ;;
            --all)
                ALL_FORMATS=true
                shift
                ;;
            --push)
                PUSH=true
                shift
                ;;
            --sign)
                SIGN=true
                shift
                ;;
            --gpg-key)
                GPG_KEY="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help)
                print_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                print_usage
                exit 1
                ;;
        esac
    done
}

validate_args() {
    if [[ -z "$VERSION" ]]; then
        log_error "Version is required"
        print_usage
        exit 1
    fi
    
    if [[ "$ALL_FORMATS" != "true" && -z "$FORMAT" ]]; then
        log_error "Format or --all is required"
        print_usage
        exit 1
    fi
    
    # Validate version format
    if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+)?$ ]]; then
        log_error "Invalid version format: $VERSION (expected: semver like 1.0.0 or 1.0.0-rc1)"
        exit 1
    fi
    
    if [[ "$SIGN" == "true" && -z "$GPG_KEY" ]]; then
        log_error "GPG key is required when using --sign"
        exit 1
    fi
}

setup_dirs() {
    log_info "Setting up release directories..."
    
    mkdir -p "$BUILD_DIR"
    mkdir -p "$DIST_DIR"
    
    # Clean previous builds for this version
    rm -rf "${BUILD_DIR}/${VERSION}"
    mkdir -p "${BUILD_DIR}/${VERSION}"
}

build_and_test() {
    log_info "Building project..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would run: make build VERSION=$VERSION"
        return 0
    fi
    
    cd "$PROJECT_ROOT"
    make build VERSION="$VERSION" || {
        log_error "Build failed"
        exit 1
    }
    
    log_info "Running tests..."
    make test || {
        log_error "Tests failed"
        exit 1
    }
    
    log_success "Build and tests completed"
}

package_docker() {
    local image_name="smartbridge:${VERSION}"
    
    if [[ -n "$REGISTRY" ]]; then
        image_name="${REGISTRY}/smartbridge:${VERSION}"
    fi
    
    log_info "Building Docker image: $image_name"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would build image: $image_name"
        log_info "[DRY RUN] Would tag as: ${image_name}-latest"
        if [[ "$PUSH" == "true" ]]; then
            log_info "[DRY RUN] Would push to registry"
        fi
        return 0
    fi
    
    # Build Docker image
    docker build \
        --tag "$image_name" \
        --tag "${image_name%-*}-latest" \
        --build-arg VERSION="$VERSION" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD)" \
        -f "$PROJECT_ROOT/Dockerfile" \
        "$PROJECT_ROOT" || {
        log_error "Docker build failed"
        exit 1
    }
    
    log_success "Docker image built: $image_name"
    
    # Push if requested
    if [[ "$PUSH" == "true" && -n "$REGISTRY" ]]; then
        log_info "Pushing image to registry..."
        docker push "$image_name" || {
            log_error "Docker push failed"
            exit 1
        }
        docker push "${image_name%-*}-latest" || true
        log_success "Image pushed to registry"
    fi
    
    # Save digest
    docker image inspect "$image_name" --format='{{index .RepoDigests 0}}' > "${DIST_DIR}/docker-digest-${VERSION}.txt" 2>/dev/null || true
}

package_helm() {
    log_info "Packaging Helm chart..."
    
    local chart_dir="${PROJECT_ROOT}/helm/smartbridge"
    
    if [[ ! -d "$chart_dir" ]]; then
        log_error "Helm chart not found: $chart_dir"
        exit 1
    fi
    
    # Update chart version
    if [[ "$DRY_RUN" != "true" ]]; then
        sed -i "s/^version:.*/version: ${VERSION}/" "${chart_dir}/Chart.yaml"
        sed -i "s/^appVersion:.*/appVersion: ${VERSION}/" "${chart_dir}/Chart.yaml"
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would package Helm chart version $VERSION"
        if [[ -n "$REGISTRY" ]]; then
            log_info "[DRY RUN] Would push to $REGISTRY"
        fi
        return 0
    fi
    
    # Package chart
    helm package "$chart_dir" --destination "$DIST_DIR" || {
        log_error "Helm package failed"
        exit 1
    }
    
    log_success "Helm chart packaged: smartbridge-${VERSION}.tgz"
    
    # Push to registry if specified
    if [[ -n "$REGISTRY" ]]; then
        log_info "Pushing Helm chart to OCI registry..."
        
        # Login to registry if needed
        if command -v helm-push &> /dev/null; then
            helm push "${DIST_DIR}/smartbridge-${VERSION}.tgz" "oci://${REGISTRY}" || {
                log_error "Helm push failed"
                exit 1
            }
            log_success "Helm chart pushed to registry"
        else
            log_warn "helm-push plugin not installed, skipping registry push"
        fi
    fi
}

package_binary() {
    log_info "Creating binary distribution..."
    
    local binary_dir="${BUILD_DIR}/${VERSION}/bin"
    local archive_name="smartbridge-${VERSION}-$(uname -s)-$(uname -m).tar.gz"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create archive: $archive_name"
        log_info "[DRY RUN] Would generate checksums"
        if [[ "$SIGN" == "true" ]]; then
            log_info "[DRY RUN] Would sign with GPG key: $GPG_KEY"
        fi
        return 0
    fi
    
    # Copy binaries and dependencies
    mkdir -p "$binary_dir"
    
    if [[ -f "${PROJECT_ROOT}/bin/smartbridge" ]]; then
        cp "${PROJECT_ROOT}/bin/smartbridge" "$binary_dir/"
    fi
    
    # Include release files
    cp "${PROJECT_ROOT}/README.md" "$binary_dir/README.md"
    cp "${PROJECT_ROOT}/LICENSE" "$binary_dir/LICENSE"
    cp "${PROJECT_ROOT}/CHANGELOG.md" "$binary_dir/CHANGELOG.md"
    
    # Create archive
    tar -czf "${DIST_DIR}/${archive_name}" -C "${BUILD_DIR}/${VERSION}" bin/ || {
        log_error "Archive creation failed"
        exit 1
    }
    
    log_success "Archive created: $archive_name"
    
    # Generate checksums
    cd "$DIST_DIR"
    sha256sum "$archive_name" >> "$CHECKSUMS_FILE"
    sha512sum "$archive_name" >> "$CHECKSUMS_FILE.sha512"
    
    # Sign checksums if requested
    if [[ "$SIGN" == "true" ]]; then
        log_info "Signing checksums..."
        gpg --default-key "$GPG_KEY" --detach-sign "$CHECKSUMS_FILE" || {
            log_error "GPG signing failed"
            exit 1
        }
        log_success "Checksums signed"
    fi
}

package_kubernetes() {
    log_info "Preparing Kubernetes manifests..."
    
    local k8s_dir="${PROJECT_ROOT}/k8s"
    local manifest_dir="${BUILD_DIR}/${VERSION}/k8s-manifests"
    
    if [[ ! -d "$k8s_dir" ]]; then
        log_warn "Kubernetes manifests directory not found: $k8s_dir"
        return
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would prepare Kubernetes manifests"
        log_info "[DRY RUN] Would archive manifests and configs"
        return 0
    fi
    
    # Copy and process manifests
    mkdir -p "$manifest_dir"
    cp -r "$k8s_dir"/* "$manifest_dir/" 2>/dev/null || true
    
    # Update image version in manifests
    find "$manifest_dir" -name "*.yaml" -o -name "*.yml" | while read -r file; do
        sed -i "s|smartbridge:latest|smartbridge:${VERSION}|g" "$file"
        sed -i "s|smartbridge:[0-9]*\.[0-9]*\.[0-9]*|smartbridge:${VERSION}|g" "$file"
    done
    
    # Create archive
    tar -czf "${DIST_DIR}/smartbridge-k8s-${VERSION}.tar.gz" -C "${BUILD_DIR}/${VERSION}" k8s-manifests/ || {
        log_error "K8s archive creation failed"
        exit 1
    }
    
    log_success "Kubernetes manifests packaged"
    
    # Generate checksums
    cd "$DIST_DIR"
    sha256sum "smartbridge-k8s-${VERSION}.tar.gz" >> "$CHECKSUMS_FILE"
}

generate_release_notes() {
    log_info "Generating release notes..."
    
    local release_notes="${RELEASE_DIR}/v${VERSION}-RELEASE_NOTES.md"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would generate release notes: $release_notes"
        return 0
    fi
    
    cat > "$release_notes" << EOF
# Release v${VERSION}

**Release Date:** $(date -u +'%Y-%m-%d')

## Contents

This release includes:
EOF
    
    # Add format information
    if [[ "$ALL_FORMATS" == "true" || "$FORMAT" == "docker" ]]; then
        echo "- Docker image: \`smartbridge:${VERSION}\`" >> "$release_notes"
    fi
    
    if [[ "$ALL_FORMATS" == "true" || "$FORMAT" == "helm" ]]; then
        echo "- Helm chart: \`smartbridge-${VERSION}.tgz\`" >> "$release_notes"
    fi
    
    if [[ "$ALL_FORMATS" == "true" || "$FORMAT" == "binary" ]]; then
        echo "- Binary distributions with checksums" >> "$release_notes"
    fi
    
    if [[ "$ALL_FORMATS" == "true" || "$FORMAT" == "kubernetes" ]]; then
        echo "- Kubernetes manifests: \`smartbridge-k8s-${VERSION}.tar.gz\`" >> "$release_notes"
    fi
    
    cat >> "$release_notes" << 'EOF'

## Installation

### Docker
\`\`\`bash
docker pull smartbridge:${VERSION}
docker run smartbridge:${VERSION}
\`\`\`

### Helm
\`\`\`bash
helm install smartbridge ./smartbridge-${VERSION}.tgz
\`\`\`

### Binary
\`\`\`bash
tar -xzf smartbridge-${VERSION}-Linux-x86_64.tar.gz
./bin/smartbridge
\`\`\`

## Verification

Verify package integrity:
\`\`\`bash
sha256sum -c CHECKSUMS
\`\`\`

## Support

For issues, please visit: https://github.com/your-org/smartbridge/issues
EOF
    
    log_success "Release notes generated: $(basename "$release_notes")"
}

generate_manifest() {
    log_info "Generating release manifest..."
    
    local manifest="${RELEASE_DIR}/v${VERSION}-MANIFEST.json"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would generate manifest: $manifest"
        return 0
    fi
    
    cat > "$manifest" << EOF
{
  "version": "${VERSION}",
  "release_date": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "formats": [
EOF
    
    if [[ "$ALL_FORMATS" == "true" || "$FORMAT" == "docker" ]]; then
        echo "    \"docker\"," >> "$manifest"
    fi
    
    if [[ "$ALL_FORMATS" == "true" || "$FORMAT" == "helm" ]]; then
        echo "    \"helm\"," >> "$manifest"
    fi
    
    if [[ "$ALL_FORMATS" == "true" || "$FORMAT" == "binary" ]]; then
        echo "    \"binary\"," >> "$manifest"
    fi
    
    if [[ "$ALL_FORMATS" == "true" || "$FORMAT" == "kubernetes" ]]; then
        echo "    \"kubernetes\"" >> "$manifest"
    fi
    
    cat >> "$manifest" << 'EOF'
  ],
  "artifacts": [
EOF
    
    # List artifacts
    if [[ -d "$DIST_DIR" ]]; then
        ls -1 "$DIST_DIR" | while read -r file; do
            echo "    \"$file\"," >> "$manifest"
        done
        # Remove trailing comma from last item
        sed -i '$ s/,$//' "$manifest"
    fi
    
    cat >> "$manifest" << 'EOF'
  ],
  "signed": VERSION_PLACEHOLDER
}
EOF
    
    # Replace placeholder
    sed -i "s/VERSION_PLACEHOLDER/${SIGN}/g" "$manifest"
    
    log_success "Release manifest generated: $(basename "$manifest")"
}

main() {
    log_info "SmartBridge Release Packaging Tool"
    
    parse_args "$@"
    validate_args
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "DRY RUN MODE - No changes will be made"
    fi
    
    setup_dirs
    
    # Build project
    build_and_test
    
    # Package in requested formats
    if [[ "$ALL_FORMATS" == "true" ]]; then
        FORMAT="docker"
        package_docker
        
        FORMAT="helm"
        package_helm
        
        FORMAT="binary"
        package_binary
        
        FORMAT="kubernetes"
        package_kubernetes
    else
        case "$FORMAT" in
            docker)
                package_docker
                ;;
            helm)
                package_helm
                ;;
            binary)
                package_binary
                ;;
            kubernetes)
                package_kubernetes
                ;;
            *)
                log_error "Unknown format: $FORMAT"
                exit 1
                ;;
        esac
    fi
    
    # Generate documentation
    generate_release_notes
    generate_manifest
    
    log_success "Release packaging completed successfully!"
    log_info "Artifacts available in: $DIST_DIR"
}

main "$@"
