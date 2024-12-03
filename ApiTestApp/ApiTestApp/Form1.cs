using System;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Windows.Forms;

namespace ApiTestApp
{
    public partial class MainForm : Form
    {
        // Set a default timeout for all HttpClient operations
        private static readonly HttpClient client = new HttpClient
        {
            Timeout = TimeSpan.FromSeconds(1000) // Adjust the timeout as needed
        };

        public MainForm()
        {
            InitializeComponent();
        }

        private async void btnLogin_Click(object sender, EventArgs e)
        {
            string apiServer = txtServer.Text.Trim();
            var username = txtUsername.Text.Trim();
            var password = txtPassword.Text.Trim();

            if (string.IsNullOrEmpty(apiServer))
            {
                MessageBox.Show("Please enter a valid server URL.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            if (string.IsNullOrEmpty(username) || string.IsNullOrEmpty(password))
            {
                MessageBox.Show("Username and Password are required.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            var loginPayload = $"{{\"username\": \"{username}\", \"password\": \"{password}\"}}";
            var content = new StringContent(loginPayload, Encoding.UTF8, "application/json");

            try
            {
                var response = await client.PostAsync($"{apiServer}/api/v1/login", content);
                response.EnsureSuccessStatusCode();
                var responseBody = await response.Content.ReadAsStringAsync();
                txtResponse.Text = responseBody;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error during login: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private async void btnUploadDocument_Click(object sender, EventArgs e)
        {
            string apiServer = txtServer.Text.Trim();
            var token = txtAuthToken.Text.Trim();
            var tcDocId = txtTcDocId.Text.Trim();

            if (string.IsNullOrEmpty(apiServer) || string.IsNullOrEmpty(token) || string.IsNullOrEmpty(tcDocId))
            {
                MessageBox.Show("Server URL, Auth Token, and Document ID are required.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            if (openFileDialog1.ShowDialog() == DialogResult.OK)
            {
                spinner.Visible = true;
                var filePath = openFileDialog1.FileName;

                using var form = new MultipartFormDataContent();
                form.Add(new StringContent(tcDocId), "tc_doc_id");
                form.Add(new ByteArrayContent(File.ReadAllBytes(filePath)), "files", Path.GetFileName(filePath));
                client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);

                try
                {
                    var response = await client.PostAsync($"{apiServer}/api/v1/upload-documents", form);
                    response.EnsureSuccessStatusCode();
                    var responseBody = await response.Content.ReadAsStringAsync();
                    txtResponse.Text = responseBody;
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Error during document upload: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
                finally
                {
                    spinner.Visible = false;
                }
            }
        }

        private async void btnDeleteDocument_Click(object sender, EventArgs e)
        {
            string apiServer = txtServer.Text.Trim();
            var token = txtAuthToken.Text.Trim();
            var tcDocId = txtTcDocId.Text.Trim();

            if (string.IsNullOrEmpty(apiServer) || string.IsNullOrEmpty(token) || string.IsNullOrEmpty(tcDocId))
            {
                MessageBox.Show("Server URL, Auth Token, and Document ID are required.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);

            try
            {
                var response = await client.DeleteAsync($"{apiServer}/api/v1/delete-document?tc_doc_id={tcDocId}");
                response.EnsureSuccessStatusCode();
                var responseBody = await response.Content.ReadAsStringAsync();
                txtResponse.Text = responseBody;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error during document deletion: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private async void btnUpdateDocument_Click(object sender, EventArgs e)
        {
            string apiServer = txtServer.Text.Trim();
            var token = txtAuthToken.Text.Trim();
            var tcDocId = txtTcDocId.Text.Trim();

            if (string.IsNullOrEmpty(apiServer) || string.IsNullOrEmpty(token) || string.IsNullOrEmpty(tcDocId))
            {
                MessageBox.Show("Server URL, Auth Token, and Document ID are required.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            if (openFileDialog1.ShowDialog() == DialogResult.OK)
            {
                spinner.Visible = true;
                var filePath = openFileDialog1.FileName;

                using var form = new MultipartFormDataContent();
                form.Add(new StringContent(tcDocId), "tc_doc_id");
                form.Add(new ByteArrayContent(File.ReadAllBytes(filePath)), "files", Path.GetFileName(filePath));
                client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);

                try
                {
                    var response = await client.PutAsync($"{apiServer}/api/v1/update-document", form);
                    response.EnsureSuccessStatusCode();
                    var responseBody = await response.Content.ReadAsStringAsync();
                    txtResponse.Text = responseBody;
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Error during document update: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
                finally
                {
                    spinner.Visible = false;
                }
            }
        }

        private async void btnCheckSLA_Click(object sender, EventArgs e)
        {
            string apiServer = txtServer.Text.Trim();
            var token = txtAuthToken.Text.Trim();
            var title = txtTitle.Text.Trim();
            var message = txtMessage.Text.Trim();

            if (string.IsNullOrEmpty(apiServer) || string.IsNullOrEmpty(token) || string.IsNullOrEmpty(title) || string.IsNullOrEmpty(message))
            {
                MessageBox.Show("All fields are required for SLA check.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            var slaPayload = $"{{\"title\": \"{title}\", \"message\": \"{message}\"}}";
            var content = new StringContent(slaPayload, Encoding.UTF8, "application/json");
            client.DefaultRequestHeaders.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);

            spinner.Visible = true;

            try
            {
                var response = await client.PostAsync($"{apiServer}/api/v1/check-sla", content);
                response.EnsureSuccessStatusCode();
                var responseBody = await response.Content.ReadAsStringAsync();

                dynamic slaData = Newtonsoft.Json.JsonConvert.DeserializeObject(responseBody);

                // Format the response
                string slaInfo = slaData.sla_info ?? "No SLA Info provided";
                string slaViolated = string.IsNullOrEmpty((string)slaData.sla_violated) ? "No" : "Yes";
                string elapsedTime = slaData.elapsed_time != null ? $"{slaData.elapsed_time} seconds" : "N/A";
                string cacheHit = slaData.cache_hit != null ? slaData.cache_hit.ToString() : "Unknown";

                string formattedResponse = $"SLA Info:\n{slaInfo}\n\n" +
                                           $"SLA Violated: {slaViolated}\n\n" +
                                           $"Elapsed Time: {elapsedTime}\n\n" +
                                           $"Cache Hit: {cacheHit}";

                // Display formatted response
                txtResponse.Text = formattedResponse;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error during SLA check: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                spinner.Visible = false;
            }
        }



        private void MainForm_Load(object sender, EventArgs e)
        {
            spinner.Visible = false;
        }
    }
}
