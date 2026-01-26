console.log("main.js loaded");

/* ================= RESUME AUTO-FILL ================= */

document.addEventListener("DOMContentLoaded", () => {
  const uploadInput = document.getElementById("resumeUpload");

  if (!uploadInput) {
    console.error("resumeUpload input not found");
    return;
  }

  uploadInput.addEventListener("change", function () {
    const file = this.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("resume", file);

    fetch("/extract_resume", {
      method: "POST",
      body: formData
    })
      .then(res => res.json())
      .then(data => {
        console.log("Extracted data:", data);

        document.getElementById("fullName").value = data.full_name || "";
        document.getElementById("email").value = data.email || "";
        document.getElementById("phone").value = data.phone || "";
        document.getElementById("location").value = data.location || "";
        document.getElementById("linkedin").value = data.linkedin || "";

        document.getElementById("summary").value = data.summary || "";
        document.getElementById("skills").value = data.skills || "";
        document.getElementById("projects").value = data.projects || "";
      })
      .catch(err => {
        console.error("Resume extraction error:", err);
        alert("Failed to extract resume data");
      });
  });
});

/* ================= SMART ATS + RADAR DASHBOARD ================= */

let atsChart = null;

async function analyzeResume() {
  const summary = document.getElementById("summary").value;
  const skills = document.getElementById("skills").value;
  const projects = document.getElementById("projects").value;
  const jd = document.getElementById("jobDescription").value;

  if (!summary && !skills && !projects) {
    alert("Please upload resume first");
    return;
  }

  if (!jd) {
    alert("Please paste job description");
    return;
  }

  const fullResumeText = `
SUMMARY:
${summary}

SKILLS:
${skills}

PROJECTS:
${projects}
`;

  try {
    const res = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        resume: fullResumeText,
        job_description: jd
      })
    });

    const data = await res.json();
    console.log("ATS Result:", data);

    /* ===== SCORE ===== */
    const scoreValue = data.overall_score ?? data.score ?? 0;
    document.getElementById("score").innerText = scoreValue;

    /* ===== KEYWORD SUGGESTIONS ===== */
    const ul = document.getElementById("suggestions");
    ul.innerHTML = "";
    (data.missing_keywords || []).forEach(word => {
      const li = document.createElement("li");
      li.innerText = "Add keyword: " + word;
      ul.appendChild(li);
    });

    /* ===== AI SECTION SUGGESTIONS ===== */
    const list = document.getElementById('aiSuggestions');
list.innerHTML = "";
data.suggestions.forEach(s => {
  const li = document.createElement('li');
  li.textContent = s;
  list.appendChild(li);
});

    /* ===== RADAR CHART ===== */
    document.getElementById('atsScore').innerText = data.ats_score + "%";

    if (data.breakdown) {
      const ctx = document.getElementById("atsChart").getContext("2d");
      if (atsChart) atsChart.destroy();

      atsChart = new Chart(ctx, {
        type: "radar",
        data: {
          labels: ["Skills", "Projects", "Education", "Keywords"],
          datasets: [{
            label: "ATS Match (%)",
            data: [
              data.breakdown.skills || 0,
              data.breakdown.projects || 0,
              data.breakdown.education || 0,
              data.breakdown.keywords || 0
            ],
            fill: true,
            backgroundColor: "rgba(108, 99, 255, 0.25)",
            borderColor: "#6C63FF",
            pointBackgroundColor: "#6C63FF"
          }]
        },
        options: {
          responsive: true,
          scales: {
            r: {
              min: 0,
              max: 100,
              ticks: { stepSize: 20 }
            }
          }
        }
      });
    }

  } catch (err) {
    console.error("ATS analysis error:", err);
    alert("Failed to analyze ATS score");
  }
}

/* ================= FORM VALIDATION ================= */

function validateForm() {
  const name = document.getElementById("fullName").value.trim();
  const email = document.getElementById("email").value.trim();
  const skills = document.getElementById("skills").value.trim();

  if (!name || !email || !skills) {
    alert("Please fill all required fields");
    return false;
  }
  return true;
}
