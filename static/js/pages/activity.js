/**
 * Activity Feed Page
 */

async function renderActivity() {
  const container = document.getElementById('activity-content');
  
  container.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
      <div style="display: flex; gap: 8px;">
        <button class="btn btn-secondary" style="background: var(--color-forest); color: white; border-color: var(--color-forest);">All Activity</button>
        <button class="btn btn-secondary">Pull Requests</button>
        <button class="btn btn-secondary">Issues</button>
        <button class="btn btn-secondary">Reviews</button>
      </div>
    </div>
    
    <div class="card" style="display: flex; flex-direction: column; gap: 24px;">
      
      <div style="display: flex; gap: 16px;">
        <div class="avatar-small" style="background: var(--color-mint); color: var(--color-forest);">MC</div>
        <div style="flex: 1;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="font-size: 15px;">
              <strong>Manas Chhabra</strong> merged a Pull Request in <strong style="color: var(--color-forest);">open-source/project-one</strong>
            </div>
            <div style="color: var(--text-muted); font-size: 13px;">2 hours ago</div>
          </div>
          <div style="margin-top: 8px; padding: 12px; background: var(--color-light-gray); border-radius: 8px; font-size: 14px;">
            Improve error handling in auth module (#142)
          </div>
        </div>
      </div>

      <div style="display: flex; gap: 16px;">
        <div class="avatar-small" style="background: var(--color-warning-light); color: var(--color-warning);">AM</div>
        <div style="flex: 1;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="font-size: 15px;">
              <strong>Ayushi Mishra</strong> closed an Issue in <strong style="color: var(--color-forest);">awesome/lib-two</strong>
            </div>
            <div style="color: var(--text-muted); font-size: 13px;">5 hours ago</div>
          </div>
          <div style="margin-top: 8px; padding: 12px; background: var(--color-light-gray); border-radius: 8px; font-size: 14px;">
            Fix typos in documentation (#89)
          </div>
        </div>
      </div>

      <div style="display: flex; gap: 16px;">
        <div class="avatar-small" style="background: #E0E7FF; color: #4F46E5;">JD</div>
        <div style="flex: 1;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="font-size: 15px;">
              <strong>Jane Doe</strong> reviewed a Pull Request in <strong style="color: var(--color-forest);">cool-tool/cli</strong>
            </div>
            <div style="color: var(--text-muted); font-size: 13px;">1 day ago</div>
          </div>
          <div style="margin-top: 8px; padding: 12px; background: var(--color-light-gray); border-radius: 8px; font-size: 14px;">
            Add validation for email field (#201)
          </div>
        </div>
      </div>

    </div>
  `;
}
