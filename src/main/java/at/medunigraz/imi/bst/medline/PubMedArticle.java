package at.medunigraz.imi.bst.medline;

import java.util.ArrayList;

public class PubMedArticle {

    public String pubMedId;
    public String docTitle;
    public String docAbstract;
    public String publicationType;
    public String language;
    public String publicationYear;
    public ArrayList<String> meshTags;
    public ArrayList<String> medlineKeywords;

    public PubMedArticle() {
        this.meshTags = new ArrayList<>();
        this.medlineKeywords = new ArrayList<>();
    }

    public PubMedArticle(String pubMedId, String docTitle, String docAbstract, String publicationType,
                         String language, String publicationYear) {
        this.pubMedId = pubMedId;
        this.docTitle = docTitle;
        this.docAbstract = docAbstract;
        this.publicationType = publicationType;
        this.language = language;
        this.publicationYear = publicationYear;
        this.meshTags = new ArrayList<>();
        this.medlineKeywords = new ArrayList<>();
    }

    @Override
    public String toString() {
        return "\nPMID: " + this.pubMedId + "\n" +
               "TITLE: " + this.docTitle + "\n" +
               "ABSTRACT: " + this.docAbstract + "\n" +
               "PUB. TYPE: " + this.publicationType + "\n" +
               "LANGUAGE: " + this.language + "\n" +
               "YEAR: " + this.publicationYear + "\n" +
               "MESHTAGS: " + this.meshTags + "\n" +
               "MEDLINE KEYWORDS: " + this.medlineKeywords;
    }
    
	public int getPublicationYear() {
		int ret = 0;
		
		if (publicationYear == null) {
			return ret;
		}

		try {
			ret = Integer.parseInt(publicationYear);
		} catch (NumberFormatException e) {
			return ret;
		}
		
		return ret;
	}
}
