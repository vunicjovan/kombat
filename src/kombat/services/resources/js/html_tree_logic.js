function toggleNode(element) {
    element.classList.toggle('expanded');
    const content = element.nextElementSibling;
    if (content) {
        content.classList.toggle('hidden');
    }
}

function formatSize(bytes) {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    return `${size.toFixed(2)} ${units[unitIndex]}`;
}

function formatTimestamp(timestamp) {
    return new Date(timestamp * 1000).toLocaleString();
}

//const hierarchyData = JSON.parse(document.body.innerHTML);
// Instead of parsing from document.body, fetch the hierarchy data from a global variable
const hierarchyData = JSON.parse(document.getElementById('hierarchy').dataset.hierarchyData);

function createTreeNode(data, name, isRoot = false) {
    const container = document.createElement('div');

    if (data.files || data.directories) {
        const header = document.createElement('div');
        header.className = 'expandable directory';
        if (!isRoot) header.classList.add('tree-node');
        header.textContent = name;
        header.onclick = () => toggleNode(header);
        container.appendChild(header);

        const content = document.createElement('div');
        content.className = 'tree-node';

        // Add files
        if (data.files) {
            Object.entries(data.files).forEach(([ext, files]) => {
                Object.entries(files).forEach(([fileName, fileData]) => {
                    const fileNode = document.createElement('div');
                    fileNode.className = 'file file-node';
                    fileNode.innerHTML = `
                        ${fileName}
                        <span class="file-ext">${ext}</span>
                        <span class="metadata">
                            (${formatSize(fileData.size_in_bytes)},
                            Created: ${formatTimestamp(fileData.timestamps.created)},
                            Modified: ${formatTimestamp(fileData.timestamps.modified)})
                        </span>
                    `;
                    content.appendChild(fileNode);
                });
            });
        }

        // Add duplicates section if exists
        if (data.duplicates) {
            const duplicatesNode = document.createElement('div');
            duplicatesNode.className = 'tree-node';
            Object.entries(data.duplicates).forEach(([hash, files]) => {
                if (files.length > 1) {
                    const dupNode = document.createElement('div');
                    dupNode.className = 'duplicate';
                    dupNode.textContent = `Duplicates: ${files.join(', ')}`;
                    duplicatesNode.appendChild(dupNode);
                }
            });
            content.appendChild(duplicatesNode);
        }

        // Add subdirectories
        if (data.directories) {
            Object.entries(data.directories).forEach(([dirName, dirData]) => {
                content.appendChild(createTreeNode(dirData, dirName));
            });
        }

        container.appendChild(content);
    }

    return container;
}

const hierarchyContainer = document.getElementById('hierarchy');
Object.entries(hierarchyData).forEach(([rootName, rootData]) => {
    hierarchyContainer.appendChild(createTreeNode(rootData, rootName, true));
});

// Expand root nodes by default
document.querySelectorAll('.expandable').forEach(node => {
    if (!node.classList.contains('tree-node')) {
        toggleNode(node);
    }
});

// Resizable divider
const divider = document.querySelector('.split-divider');
const left = document.querySelector('.split-left');
let x = 0;
let leftWidth = 0;

divider.addEventListener('mousedown', function(e) {
    x = e.clientX;
    leftWidth = left.getBoundingClientRect().width;
    document.addEventListener('mousemove', moveDivider, false);
    document.addEventListener('mouseup', stopDivider, false);
});

function moveDivider(e) {
    const dx = e.clientX - x;
    const newLeftWidth = leftWidth + dx;
    left.style.width = `${newLeftWidth}px`;
}

function stopDivider() {
    document.removeEventListener('mousemove', moveDivider, false);
    document.removeEventListener('mouseup', stopDivider, false);
}
