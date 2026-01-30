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

/* ================= ANALYZE RESUME → PASS DATA TO NEW PAGE ================= */

async function analyzeResume() {
  try {
    const summary = document.getElementById("summary")?.value || "";
    const skills = document.getElementById("skills")?.value || "";
    const projects = document.getElementById("projects")?.value || "";
    const jd = document.getElementById("jobDescription")?.value || "";

    if (!summary && !skills && !projects) {
      alert("Please upload or fill resume first");
      return;
    }

    if (!jd.trim()) {
      alert("Please paste job description");
      return;
    }

    // 🔹 Build full resume text
    const fullResumeText = `
SUMMARY:
${summary}

SKILLS:
${skills}

PROJECTS:
${projects}
`;

    // 🔹 Store data for next page
    const payload = {
      resume: fullResumeText,
      job_description: jd
    };

    sessionStorage.setItem("ats_payload", JSON.stringify(payload));

    // 🔹 Redirect to result page
    window.location.href = "/ats-result";

  } catch (err) {
    console.error("Analyze redirect error:", err);
    alert("Unable to proceed with ATS analysis");
  }
}

/* ================= FORM VALIDATION (OPTIONAL) ================= */

function validateForm() {
  const name = document.getElementById("fullName")?.value.trim();
  const email = document.getElementById("email")?.value.trim();
  const skills = document.getElementById("skills")?.value.trim();

  if (!name || !email || !skills) {
    alert("Please fill all required fields");
    return false;
  }
  return true;
}
