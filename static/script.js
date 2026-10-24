let latest = null;

document.getElementById("analyzeBtn").addEventListener("click", async function () {

    const button = this;
    const status = document.getElementById("status");

    button.disabled = true;
    status.textContent = " Analyzing...";

    try {

        const code1 = document.getElementById("code1").value.trim();
        const code2 = document.getElementById("code2").value.trim();
        const file1 = document.getElementById("file1").files[0];
        const file2 = document.getElementById("file2").files[0];

        // A pasted code block takes priority over a selected file.
        if (!code1 && !file1) {
            alert("Please enter or upload Student 1 code.");
            return;
        }

        if (!code2 && !file2) {
            alert("Please enter or upload Student 2 code.");
            return;
        }

        const formData = new FormData();

        if (code1) {
            formData.append("code1", code1);
        } else {
            formData.append("file1", file1);
        }

        if (code2) {
            formData.append("code2", code2);
        } else {
            formData.append("file2", file2);
        }


        const response = await fetch(
            "/analyze",
            {
                method: "POST",
                body: formData
            }
        );


        const data = await response.json();


        if (!response.ok) {
            throw new Error(
                data.error || "Analysis failed"
            );
        }


        latest = data;


        // Show result
        document
            .getElementById("result")
            .classList
            .remove("hidden");


        document.getElementById(
            "overall"
        ).textContent =
            data.overall + "%";

        document.getElementById(
            "dissimilarity"
        ).textContent =
            data.dissimilarity + "%";


        document.getElementById(
            "token"
        ).textContent =
            data.token_similarity + "%";


        document.getElementById(
            "ast"
        ).textContent =
            data.ast_similarity + "%";


        document.getElementById(
            "semantic"
        ).textContent =
            data.ai_similarity + "%";


        const risk = data.overall >= 70 ? "High" : data.overall >= 30 ? "Medium" : "Low";

        document.getElementById(
            "risk"
        ).textContent =
            risk;

        const interpretations = {
            High: "High review priority: substantial similarity was found. Inspect matched lines and context; this score alone does not establish plagiarism.",
            Medium: "Medium review priority: some similarity was found. Compare the matching lines and consider common assignment requirements.",
            Low: "Low review priority: little similarity was found by these heuristics. This does not prove the code is fully independent."
        };

        document.getElementById(
            "interpretation"
        ).textContent =
            interpretations[risk] || "Review the matching lines and source context before drawing a conclusion.";


        // Matching lines
        const table =
            document.getElementById(
                "matches"
            );


        table.innerHTML =
            `
            <tr>
                <th>Code 1</th>
                <th>Code 2</th>
                <th>Similarity</th>
            </tr>
            `;


        data.matches.forEach(
            function (match) {

                table.innerHTML +=
                    `
                    <tr>
                        <td>${match.line1}</td>
                        <td>${match.line2}</td>
                        <td>${match.similarity}%</td>
                    </tr>
                    `;
            }
        );


    } catch (error) {

        alert(
            error.message
        );

    } finally {

        button.disabled = false;
        status.textContent = "";
    }

});


document.getElementById("pdfBtn").addEventListener(
    "click",
    async function () {

        if (!latest) {
            alert(
                "Analyze the code first."
            );
            return;
        }


        try {

            const response =
                await fetch(
                    "/generate_report",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify(
                                latest
                            )
                    }
                );


            if (!response.ok) {
                throw new Error(
                    "Could not generate PDF."
                );
            }


            const blob =
                await response.blob();


            const url =
                window.URL.createObjectURL(
                    blob
                );


            const link =
                document.createElement(
                    "a"
                );

            link.href = url;

            link.download =
                "plagiarism_report.pdf";

            document.body.appendChild(
                link
            );

            link.click();

            link.remove();

            window.URL.revokeObjectURL(
                url
            );


        } catch (error) {

            alert(
                error.message
            );
        }

    }
);


const multipleFilesInput = document.getElementById("multipleFiles");
const selectedFilesLabel = document.getElementById("selectedFiles");
const clearFilesButton = document.getElementById("clearFilesBtn");
let selectedComparisonFiles = [];

multipleFilesInput.addEventListener("change", function () {
    selectedComparisonFiles.push(...Array.from(this.files));
    this.value = "";

    selectedFilesLabel.textContent = selectedComparisonFiles.length
        ? selectedComparisonFiles.length + " file(s) selected: " + selectedComparisonFiles.map(function (file) {
            return file.name;
        }).join(", ")
        : "No files selected.";
    clearFilesButton.disabled = selectedComparisonFiles.length === 0;
    document.getElementById("multiResult").classList.add("hidden");
    document.getElementById("multiStatus").textContent = "";
});


clearFilesButton.addEventListener("click", function () {
    selectedComparisonFiles = [];
    selectedFilesLabel.textContent = "No files selected.";
    clearFilesButton.disabled = true;
    document.getElementById("multiResult").classList.add("hidden");
    document.getElementById("multiStatus").textContent = "";
});


document.getElementById("compareMultipleBtn").addEventListener("click", async function () {
    const button = this;
    const files = selectedComparisonFiles.slice();
    const status = document.getElementById("multiStatus");

    if (files.length < 2) {
        status.textContent = "Select at least two files to compare.";
        return;
    }

    button.disabled = true;
    status.textContent = "Comparing files...";

    try {
        const formData = new FormData();
        files.forEach(function (file) {
            formData.append("files", file);
        });

        const response = await fetch("/compare_multiple", {
            method: "POST",
            body: formData
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Multiple-file comparison failed.");
        }

        const pairTable = document.getElementById("pairResults");
        pairTable.replaceChildren();

        const pairHeaders = [
            "File 1",
            "File 2",
            "Similarity",
            "Dissimilarity",
            "Review priority",
            "Token",
            "Structure",
            "Semantic-style",
            "Matching lines"
        ];
        const pairHeaderRow = document.createElement("tr");
        pairHeaders.forEach(function (label) {
            const header = document.createElement("th");
            header.textContent = label;
            pairHeaderRow.appendChild(header);
        });
        pairTable.appendChild(pairHeaderRow);

        data.comparisons.forEach(function (comparison) {
            const row = document.createElement("tr");
            const values = [
                comparison.file1,
                comparison.file2,
                Number(comparison.overall).toFixed(2) + "%",
                Number(comparison.dissimilarity).toFixed(2) + "%",
                comparison.risk,
                Number(comparison.token_similarity).toFixed(2) + "%",
                Number(comparison.ast_similarity).toFixed(2) + "%",
                Number(comparison.ai_similarity).toFixed(2) + "%",
                comparison.matching_lines
            ];

            values.forEach(function (value) {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            });
            pairTable.appendChild(row);
        });

        const table = document.getElementById("similarityMatrix");
        table.replaceChildren();

        const headerRow = document.createElement("tr");
        const corner = document.createElement("th");
        corner.textContent = "File";
        headerRow.appendChild(corner);

        data.files.forEach(function (fileName) {
            const header = document.createElement("th");
            header.textContent = fileName;
            headerRow.appendChild(header);
        });
        table.appendChild(headerRow);

        data.matrix.forEach(function (scores, rowIndex) {
            const row = document.createElement("tr");
            const rowHeader = document.createElement("th");
            rowHeader.textContent = data.files[rowIndex];
            row.appendChild(rowHeader);

            scores.forEach(function (score, columnIndex) {
                const cell = document.createElement("td");
                cell.textContent = rowIndex === columnIndex
                    ? "-"
                    : Number(score).toFixed(2) + "%";
                row.appendChild(cell);
            });
            table.appendChild(row);
        });

        document.getElementById("multiResult").classList.remove("hidden");
        status.textContent = "Compared " + data.files.length + " files across " + data.comparisons.length + " unique pairs.";
    } catch (error) {
        status.textContent = error.message;
    } finally {
        button.disabled = false;
    }
});