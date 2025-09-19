document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities", { cache: "no-store" });
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Reset activity select options (keep placeholder)
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        // Build participants HTML: bulleted list with small badges and tooltip for full email
        const participantsHTML = details.participants.length
          ? `<div class="participants-section">
               <h5 class="participants-title">Participants (${details.participants.length})</h5>
               <ul class="participants-list">
                 ${details.participants
                   .map(
                     (p) =>
                       `<li class="participant-item" title="${p}"><span class="participant-badge">${formatParticipant(
                         p
                       )}</span><button class="unregister-btn" data-email="${p}" aria-label="Unregister ${formatParticipant(
                         p
                       )}">✖</button></li>`
                   )
                   .join("")}
               </ul>
             </div>`
          : `<p class="no-participants">No participants yet. Be the first!</p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          ${participantsHTML}
        `;

        // Attach activity name to the card so event handlers can identify it
        activityCard.dataset.activity = name;
        activitiesList.appendChild(activityCard);

        // Delegated click handler for unregister buttons inside this activity card
        activityCard.addEventListener("click", async (e) => {
          const btn = e.target.closest(".unregister-btn");
          if (!btn) return;

          const email = btn.dataset.email;
          const activityName = activityCard.dataset.activity;

          if (!email || !activityName) return;

          if (!confirm(`Unregister ${email} from ${activityName}?`)) return;

          try {
            const resp = await fetch(
              `/activities/${encodeURIComponent(activityName)}/participants?email=${encodeURIComponent(email)}`,
              { method: "DELETE" }
            );

            const result = await resp.json();
            if (resp.ok) {
              messageDiv.textContent = result.message;
              messageDiv.className = "success";
              // Refresh the activities list so the participants section updates immediately
              await fetchActivities();
            } else {
              messageDiv.textContent = result.detail || "An error occurred while unregistering";
              messageDiv.className = "error";
            }

            messageDiv.classList.remove("hidden");
            setTimeout(() => messageDiv.classList.add("hidden"), 5000);
          } catch (err) {
            console.error("Error unregistering:", err);
            messageDiv.textContent = "Failed to unregister. Please try again.";
            messageDiv.className = "error";
            messageDiv.classList.remove("hidden");
          }
        });
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Small helper to turn an email into a nicer display name (e.g. "jane.doe@..." -> "Jane Doe")
  function formatParticipant(email) {
    const local = (email || "").split("@")[0] || "";
    const parts = local.split(/[._-]+/).filter(Boolean);
    const name = parts.map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join(" ");
    return name || email;
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();

        // Refresh the activities list so the participants section updates immediately
        // Use await to ensure the UI reflects the server's updated state before
        // continuing (and avoid relying on any cached GET responses).
        await fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();

});
