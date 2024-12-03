namespace ApiTestApp
{
    partial class MainForm
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            txtUsername = new TextBox();
            txtPassword = new TextBox();
            btnLogin = new Button();
            txtAuthToken = new TextBox();
            txtTcDocId = new TextBox();
            btnUploadDocument = new Button();
            btnDeleteDocument = new Button();
            btnUpdateDocument = new Button();
            txtTitle = new TextBox();
            txtMessage = new TextBox();
            btnCheckSLA = new Button();
            txtResponse = new TextBox();
            openFileDialog1 = new OpenFileDialog();
            txtServer = new TextBox();
            spinner = new PictureBox();
            ((System.ComponentModel.ISupportInitialize)spinner).BeginInit();
            SuspendLayout();
            // 
            // txtUsername
            // 
            txtUsername.Location = new Point(12, 48);
            txtUsername.Name = "txtUsername";
            txtUsername.PlaceholderText = "Username";
            txtUsername.Size = new Size(480, 23);
            txtUsername.TabIndex = 0;
            txtUsername.Text = "demo";
            // 
            // txtPassword
            // 
            txtPassword.Location = new Point(12, 77);
            txtPassword.Name = "txtPassword";
            txtPassword.PlaceholderText = "Password";
            txtPassword.Size = new Size(480, 23);
            txtPassword.TabIndex = 1;
            txtPassword.Text = "demo";
            txtPassword.UseSystemPasswordChar = true;
            // 
            // btnLogin
            // 
            btnLogin.Location = new Point(498, 48);
            btnLogin.Name = "btnLogin";
            btnLogin.Size = new Size(100, 52);
            btnLogin.TabIndex = 2;
            btnLogin.Text = "Login";
            btnLogin.UseVisualStyleBackColor = true;
            btnLogin.Click += btnLogin_Click;
            // 
            // txtAuthToken
            // 
            txtAuthToken.Location = new Point(12, 118);
            txtAuthToken.Multiline = true;
            txtAuthToken.Name = "txtAuthToken";
            txtAuthToken.PlaceholderText = "Bearer Token";
            txtAuthToken.Size = new Size(586, 50);
            txtAuthToken.TabIndex = 3;
            // 
            // txtTcDocId
            // 
            txtTcDocId.Location = new Point(12, 174);
            txtTcDocId.Name = "txtTcDocId";
            txtTcDocId.PlaceholderText = "Document ID";
            txtTcDocId.Size = new Size(480, 23);
            txtTcDocId.TabIndex = 4;
            // 
            // btnUploadDocument
            // 
            btnUploadDocument.Location = new Point(498, 174);
            btnUploadDocument.Name = "btnUploadDocument";
            btnUploadDocument.Size = new Size(100, 23);
            btnUploadDocument.TabIndex = 5;
            btnUploadDocument.Text = "Upload";
            btnUploadDocument.UseVisualStyleBackColor = true;
            btnUploadDocument.Click += btnUploadDocument_Click;
            // 
            // btnDeleteDocument
            // 
            btnDeleteDocument.Location = new Point(498, 203);
            btnDeleteDocument.Name = "btnDeleteDocument";
            btnDeleteDocument.Size = new Size(100, 23);
            btnDeleteDocument.TabIndex = 6;
            btnDeleteDocument.Text = "Delete";
            btnDeleteDocument.UseVisualStyleBackColor = true;
            btnDeleteDocument.Click += btnDeleteDocument_Click;
            // 
            // btnUpdateDocument
            // 
            btnUpdateDocument.Location = new Point(498, 232);
            btnUpdateDocument.Name = "btnUpdateDocument";
            btnUpdateDocument.Size = new Size(100, 23);
            btnUpdateDocument.TabIndex = 7;
            btnUpdateDocument.Text = "Update";
            btnUpdateDocument.UseVisualStyleBackColor = true;
            btnUpdateDocument.Click += btnUpdateDocument_Click;
            // 
            // txtTitle
            // 
            txtTitle.Location = new Point(12, 261);
            txtTitle.Name = "txtTitle";
            txtTitle.PlaceholderText = "SLA Title";
            txtTitle.Size = new Size(480, 23);
            txtTitle.TabIndex = 8;
            txtTitle.Text = "Πρόβλημα";
            // 
            // txtMessage
            // 
            txtMessage.Location = new Point(12, 290);
            txtMessage.Multiline = true;
            txtMessage.Name = "txtMessage";
            txtMessage.PlaceholderText = "SLA Message";
            txtMessage.Size = new Size(480, 50);
            txtMessage.TabIndex = 9;
            txtMessage.Text = "Σήμερα παρουσιάστηκε πρόβλημα με την βάση δεδομένων. Παρακαλώ για την επίλυση.";
            // 
            // btnCheckSLA
            // 
            btnCheckSLA.Location = new Point(498, 317);
            btnCheckSLA.Name = "btnCheckSLA";
            btnCheckSLA.Size = new Size(100, 23);
            btnCheckSLA.TabIndex = 10;
            btnCheckSLA.Text = "Check SLA";
            btnCheckSLA.UseVisualStyleBackColor = true;
            btnCheckSLA.Click += btnCheckSLA_Click;
            // 
            // txtResponse
            // 
            txtResponse.Location = new Point(12, 375);
            txtResponse.Multiline = true;
            txtResponse.Name = "txtResponse";
            txtResponse.ReadOnly = true;
            txtResponse.ScrollBars = ScrollBars.Vertical;
            txtResponse.Size = new Size(586, 233);
            txtResponse.TabIndex = 11;
            // 
            // txtServer
            // 
            txtServer.Location = new Point(12, 12);
            txtServer.Name = "txtServer";
            txtServer.Size = new Size(586, 23);
            txtServer.TabIndex = 12;
            txtServer.Text = "http://192.168.1.218:8008";
            // 
            // spinner
            // 
            spinner.Image = Properties.Resources.loading_gif;
            spinner.Location = new Point(527, 268);
            spinner.Name = "spinner";
            spinner.Size = new Size(44, 43);
            spinner.SizeMode = PictureBoxSizeMode.StretchImage;
            spinner.TabIndex = 13;
            spinner.TabStop = false;
            spinner.Visible = false;
            // 
            // MainForm
            // 
            AutoScaleDimensions = new SizeF(7F, 15F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(610, 620);
            Controls.Add(spinner);
            Controls.Add(txtServer);
            Controls.Add(txtResponse);
            Controls.Add(btnCheckSLA);
            Controls.Add(txtMessage);
            Controls.Add(txtTitle);
            Controls.Add(btnUpdateDocument);
            Controls.Add(btnDeleteDocument);
            Controls.Add(btnUploadDocument);
            Controls.Add(txtTcDocId);
            Controls.Add(txtAuthToken);
            Controls.Add(btnLogin);
            Controls.Add(txtPassword);
            Controls.Add(txtUsername);
            Name = "MainForm";
            StartPosition = FormStartPosition.CenterScreen;
            Text = "API Test App";
            Load += MainForm_Load;
            ((System.ComponentModel.ISupportInitialize)spinner).EndInit();
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion

        private System.Windows.Forms.TextBox txtUsername;
        private System.Windows.Forms.TextBox txtPassword;
        private System.Windows.Forms.Button btnLogin;
        private System.Windows.Forms.TextBox txtAuthToken;
        private System.Windows.Forms.TextBox txtTcDocId;
        private System.Windows.Forms.Button btnUploadDocument;
        private System.Windows.Forms.Button btnDeleteDocument;
        private System.Windows.Forms.Button btnUpdateDocument;
        private System.Windows.Forms.TextBox txtTitle;
        private System.Windows.Forms.TextBox txtMessage;
        private System.Windows.Forms.Button btnCheckSLA;
        private System.Windows.Forms.TextBox txtResponse;
        private System.Windows.Forms.OpenFileDialog openFileDialog1;
        private TextBox txtServer;
        private PictureBox spinner;
    }
}
