GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

GMAIL_QUERY = (
    "newer_than:7d "
    "-in:trash "
    "-in:sent "
    "-in:drafts "
    "("
    "subject:application OR subject:applied OR subject:interview OR "
    "subject:candidate OR subject:position OR subject:hiring OR "
    "subject:recruiter OR subject:job OR subject:opportunity OR "
    "subject:resume OR subject:shortlisted OR subject:assessment OR "
    "subject:offer OR subject:rejection OR "
    "from:greenhouse.io OR from:lever.co OR from:workday.com OR "
    "from:icims.com OR from:myworkdayjobs.com OR from:smartrecruiters.com OR "
    "from:ashbyhq.com OR from:jobvite.com OR from:taleo.net OR "
    "from:noreply OR from:no-reply OR "
    "category:promotions OR in:spam"
    ")"
)

GMAIL_LABEL_NAME = "Jobs/Positive"
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

MAX_EMAILS_PER_RUN = 100
CLASSIFICATION_BATCH_SIZE = 10
BODY_SNIPPET_LENGTH = 500

CLAUDE_MODEL = "claude-haiku-4-5"
